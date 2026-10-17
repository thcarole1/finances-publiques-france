# Contrats et tolérances

- **Contrats de schéma (QC-B01)** : déclarés au plus près des modèles, dans les fichiers
  `transform/models/**/_*.yml` (`contract: enforced: true`). dbt refuse de construire une table
  dont les colonnes ou les types s'écartent du contrat.
- **Tolérances des contrôles comptables** (QC-B03 à QC-B12, QC-A01 à QC-A09) : centralisées dans
  `tolerances.yml`, lues par les tests dbt à partir du lot 1.
