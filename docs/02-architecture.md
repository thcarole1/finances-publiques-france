# 02 — Architecture

## 1. Vue d'ensemble

```
 Sources (API SDMX, API Opendatasoft, fichiers CSV/XLSX publiés)
        │
        ▼
 ingestion/  ── Python : un connecteur par source, aucune transformation métier
        │
        ▼
 data/raw/<source>/<jeu>/<date_collecte>/   (instantané brut + manifeste)  → archivé en Release
        │
        ▼
 transform/  ── normalisation, codification, conversions, consolidation  (dbt-duckdb, voir 11)
        │        └── contrôles qualité : contrats de schéma + règles métier (bloquants)
        ▼
 data/curated/<table>/   (Parquet, une table par fait ou dimension du modèle)
        │
        ▼
 powerbi/  ── modèle sémantique TMDL (mode Import) + rapport PBIR
```

## 2. Couches de données

| Couche | Emplacement | Contenu | Versionné dans Git ? |
|---|---|---|---|
| **Brut** | `data/raw/` | Fichiers exactement tels que téléchargés + `manifest.json` (URL, date, empreinte SHA-256, taille, paramètres de la requête) | Non : archivé en **Release GitHub** datée |
| **Préparé** (*staging*) | `data/staging/` | Données typées, colonnes renommées, codes normalisés, une table par jeu source | Non : recalculable |
| **Référentiels** | `data/reference/` | Nomenclatures et correspondances maintenues à la main (COFOG, SEC, payeurs, LOLF → COFOG, pays…) | **Oui** (CSV, petits, relus en PR) |
| **Modèle** (*curated*) | `data/curated/` | Une table Parquet par table du modèle Power BI | Oui si < 50 Mo par fichier, sinon Release (voir § 4) |
| **Scénarios** | `scenarios/` | Scénarios personnels en YAML | **Oui** |

Règle : **les couches *brut* et *référentiels* sont les seules sources de vérité.** Tout le reste
doit pouvoir être reconstruit par le pipeline.

## 3. Millésimes (historisation)

- Chaque collecte crée un **instantané** identifié par `source × jeu × date_collecte`.
- Un **millésime** (`Dim_Millesime`) est la version d'une donnée telle que publiée par son
  producteur. Il est daté par la date de publication quand elle est connue, sinon par la date
  de collecte.
- Les instantanés ne sont **jamais modifiés ni supprimés**. Une correction se fait par un nouvel
  instantané.
- Le modèle charge par défaut le **dernier millésime** de chaque source. L'historique complet des
  millésimes n'est chargé que pour les **agrégats clés** (voir `05`, `Fait_Revisions`) et pour
  les **prévisions** (`Fait_Hypotheses`), afin de maîtriser le volume.

## 4. Stockage et volumétrie

GitHub limite les fichiers à 100 Mo et un dépôt lourd devient lent. Stratégie :

| Données | Volume estimé | Stockage |
|---|---|---|
| Référentiels, scénarios, code, modèle TMDL | < 5 Mo | Git |
| Faits nationaux et internationaux (curated) | 10–80 Mo | Git (Parquet compressé) si < 50 Mo par fichier, sinon Release |
| Collectivités et fiscalité locale (curated) | 100–400 Mo **[À confirmer]** | Release `curated-AAAA.MM.JJ`, Parquet partitionné par année |
| Instantanés bruts | croissant | Release `raw-<source>-AAAA.MM.JJ` |

Les Releases sont préférées à **Git LFS** dont le quota gratuit (stockage et bande passante)
est limité et consommé à chaque clone.

## 5. Chargement dans Power BI

- **Mode Import** pour tout le modèle (volumes compatibles, DAX complet, groupes de calcul).
- Un paramètre Power Query `ModeSource` choisit l'origine des fichiers Parquet :
  - `Local` : dossier `data/curated` d'un clone du dépôt (développement) ;
  - `GitHub` : URL des fichiers bruts du dépôt et des assets de Release (actualisation sans
    clone, y compris dans le service Power BI si le dépôt est public).
- Une fonction Power Query unique `fnLireParquet(nomTable)` centralise la lecture.
- Aucune transformation métier dans Power Query : seulement la lecture et le typage.
  Toute la logique vit dans `transform/`, testée et versionnée.

## 6. Outillage

| Besoin | Outil proposé |
|---|---|
| Langage | Python 3.12, dépendances gérées avec `uv` |
| Collecte SDMX (Eurostat, OCDE, BCE, INSEE) | `sdmx1` ou appels HTTP directs + `pandas`/`polars` |
| Transformations | **dbt-duckdb** (SQL testé et documenté) — voir décision D1 |
| Format | Parquet (`pyarrow`), compression ZSTD |
| Qualité | tests dbt + contrats de schéma (`contracts/*.yml`) + règles métier SQL |
| Tests de code | `pytest`, `ruff` |
| Orchestration | GitHub Actions (planifié + manuel) |
| Power BI | PBIP : modèle **TMDL**, rapport **PBIR** |

## 7. Orchestration (GitHub Actions)

| Workflow | Déclenchement | Rôle |
|---|---|---|
| `ci.yml` | chaque PR | lint, tests unitaires, validation des référentiels et des scénarios YAML |
| `collecte.yml` | planifié + manuel | collecte → archivage brut → transformation → contrôles → PR de données |
| `qualite.yml` | appelé par `collecte.yml` | exécution des contrôles ; **échec = arrêt et alerte** |

Calendrier de collecte (par défaut, ajustable dans le workflow) :

| Fréquence | Moment | Sources |
|---|---|---|
| Hebdomadaire | lundi | Taux de marché, AFT (encours, échéancier) |
| Mensuelle | début de mois | Situation budgétaire de l'État, Banque de France |
| Trimestrielle | fin mars, juin, sept., déc. | Comptes et dette trimestriels (INSEE, Eurostat) |
| Semestrielle | fin avril, fin octobre | Notifications de déficit et dette (Eurostat), FMI WEO, prévisions de la Commission |
| Annuelle | fin mai, puis octobre | Comptes annuels INSEE, PLF/PLFSS, OFGL, fiscalité locale, redistribution |

**La collecte n'écrit jamais directement sur `main`** : elle ouvre une pull request de données
avec le rapport des contrôles. En cas d'échec bloquant, aucune PR n'est ouverte et une *issue*
d'alerte est créée.

## 8. Organisation du dépôt

```
finances-publiques-france/
├── README.md
├── docs/                         spécification, méthodologie, glossaire
├── ingestion/
│   ├── common/                   client HTTP, manifeste, archivage
│   └── sources/<source>.py       un connecteur par source
├── transform/                    projet dbt (models/staging, models/marts, tests)
├── contracts/                    contrats de schéma des tables du modèle (YAML)
├── data/
│   ├── reference/                référentiels versionnés (CSV)
│   ├── raw/                      (ignoré par Git)
│   ├── staging/                  (ignoré par Git)
│   └── curated/                  tables du modèle (Parquet)
├── scenarios/                    scénarios personnels (YAML)
├── projection/                   moteur de projection de dette (Python)
├── powerbi/
│   ├── FinancesPubliques.SemanticModel/   (TMDL)
│   └── FinancesPubliques.Report/          (PBIR)
├── tests/
└── .github/workflows/
```

## 9. Sécurité

- Clés d'API (INSEE, Banque de France…) uniquement dans les **secrets GitHub** et un fichier
  `.env` local ignoré par Git. Un `.env.example` documente les variables attendues.
- Le workflow de collecte n'utilise que les permissions minimales (`contents: write`,
  `pull-requests: write`, `issues: write`).
- Aucune donnée personnelle n'est collectée. Les futures données de ménages types (OpenFisca)
  seront fictives ; une situation réelle ne sera jamais versionnée dans un dépôt public.
