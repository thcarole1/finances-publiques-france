# Finances publiques de la France — modèle de données et dashboard Power BI

**Qui paie, combien, et où va l'argent ?**

Ce dépôt construit un modèle de données ouvert et versionné sur les finances publiques françaises,
comparées à l'Union européenne et aux grands pays de l'OCDE, ainsi qu'un rapport Power BI
pédagogique pour l'explorer et y tester des scénarios budgétaires.

## Périmètre

- **Toutes les administrations publiques** (État et organismes centraux, collectivités locales,
  Sécurité sociale), en vues consolidée et non consolidée, avec les transferts entre elles.
- **Recettes** par type de prélèvement, par payeur et par niveau de vie (redistribution).
- **Dépenses** par fonction (COFOG, 2 niveaux) croisées avec la nature économique (SEC 2010).
- **Dette** : stock, charge d'intérêts, taux, détenteurs, maturité, échéancier de l'AFT.
- **Budgets votés et exécutés** de l'État (LOLF) et de la Sécurité sociale (LFSS, ONDAM).
- **Collectivités** jusqu'à la commune, fiscalité locale comprise.
- **Scénarios** : simulations statiques, projections de dette, trajectoires officielles,
  bibliothèque de scénarios personnels, historique des prévisions.
- **Temps** : annuel depuis 1995, trimestriel pour la période récente.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `docs/` | Spécification, choix méthodologiques, glossaire |
| `ingestion/` | Scripts de collecte par source *(lot 1 et suivants)* |
| `transform/` | Transformations vers le modèle *(lot 1 et suivants)* |
| `data/` | Référentiels et données préparées *(voir `docs/02-architecture.md`)* |
| `scenarios/` | Bibliothèque de scénarios versionnés |
| `powerbi/` | Projet Power BI (format PBIP / TMDL) |
| `.github/workflows/` | Collecte planifiée et contrôles qualité |
| `scripts/` | Construction du modèle, validation des scénarios |
| `contracts/` | Tolérances des contrôles qualité |

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/) (installe Python 3.12 et les dépendances).

```bash
uv sync                                      # dépendances
./scripts/construire.sh                      # référentiels → modèles → tests → data/curated/*.parquet
uv run pytest                                # tests unitaires
uv run python scripts/valider_scenarios.py   # validation des scénarios
```

Sous Windows, lancer `construire.sh` depuis Git Bash, ou directement :
`uv run dbt build --project-dir transform --profiles-dir transform`
(après avoir créé les dossiers `data/staging` et `data/curated`).

Power BI : voir [`powerbi/README.md`](powerbi/README.md).

## Point d'entrée

Commencer par [`docs/README.md`](docs/README.md).

## Sources et licences

Les données proviennent de producteurs publics (INSEE, Eurostat, OCDE, AFT, DGFiP, OFGL…),
réutilisées conformément à leurs licences. Voir [`docs/03-sources-et-licences.md`](docs/03-sources-et-licences.md).

## Licence

Le **code** est publié sous licence [MIT](LICENSE). Les **données** restent soumises aux licences
de leurs producteurs respectifs (voir ci-dessus).
