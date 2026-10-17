# 10 — Conventions

## 1. Nommage

| Objet | Convention | Exemple |
|---|---|---|
| Tables de faits | `Fait_<Sujet>` | `Fait_Depenses_Fonction` |
| Dimensions | `Dim_<Sujet>` | `Dim_Sous_Secteur` |
| Ponts / correspondances | `Map_<A>_<B>` | `Map_Prelevement_Payeur` |
| Tables de présentation | `Pres_<Sujet>` | `Pres_Flux_Sankey` |
| Paramètres What-if / tables déconnectées | `Param_<Sujet>` | `Param_Delta_TVA` |
| Groupes de calcul | `CG_<Sujet>` | `CG_Unite` |
| Paramètres de champ | `FP_<Sujet>` | `FP_Axe_Depense` |
| Colonnes (Parquet et modèle) | `snake_case`, sans accents | `valeur_meur`, `date_id` |
| Colonnes visibles dans le rapport | Nom d'affichage en français via la propriété de colonne | « Montant (M€) » |
| Mesures | Français, unité entre parenthèses | `Dette (% PIB)` |
| Fichiers Python | `snake_case.py` | `eurostat.py` |

Les tables et colonnes techniques (clés, `millesime_id`…) sont **masquées** dans le modèle.

## 2. Unités et signes

- Montants stockés en **millions** (M€ ou monnaie nationale) ; jamais en milliards dans les données.
- **Dépenses et recettes positives.** Le signe n'apparaît que dans les soldes
  (solde négatif = déficit) et dans `Fait_Redistribution` via `Dim_Flux_Redistribution[signe]`.
- Taux et ratios stockés en **pourcentage** (ex. `3.5` pour 3,5 %) dans les faits d'hypothèses ;
  les mesures DAX renvoient des fractions (`0.035`) formatées en %.
- Dates : ISO 8601 (`AAAA-MM-JJ`) dans les fichiers.

## 3. Git et pull requests

- Branche principale `main`, toujours dans un état cohérent ; **pas de commit direct**.
- Branches : `spec/…`, `feat/lot-N-…`, `fix/…`, `data/collecte-AAAA-MM-JJ` (PR de données
  automatiques), `scenario/…`.
- Messages de commit : style *Conventional Commits* en français
  (`feat(ingestion): connecteur Eurostat gov_10a_exp`).
- Chaque PR décrit : ce qui change, comment le tester dans Power BI Desktop, les contrôles qualité.
- **Opérations destructives** (suppression de fichiers ou de branches, réécriture d'historique,
  purge de Releases) : audit préalable, avertissement explicite des risques et proposition de
  sauvegarde avant toute exécution, et uniquement avec ton accord.

## 4. Versions

- Le projet suit des versions `MAJEUR.MINEUR.CORRECTIF`, une version mineure par lot livré.
- Les Releases de données sont nommées `curated-AAAA.MM.JJ` et `raw-<source>-AAAA.MM.JJ`.
- Un fichier `CHANGELOG.md` récapitule les évolutions du modèle (tables, colonnes, mesures).

## 5. Documentation

- Toute nouvelle table : contrat dans `contracts/`, description dans `05`, entrée dans le
  dictionnaire de données généré.
- Toute nouvelle notion économique visible dans le rapport : entrée dans `glossaire.md`.
- Toute nouvelle source : fiche `docs/sources/<source>.md` (accès, licence, particularités,
  pièges connus).
