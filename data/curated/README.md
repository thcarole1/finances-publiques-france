# Tables du modèle (Parquet)

Produites par `./scripts/construire.sh` (dbt) — **ne pas modifier à la main**.
Un fichier par table du modèle Power BI ; les grandes tables (lot 7) seront partitionnées et
publiées en Release (docs/02-architecture.md, § 4).

| Fichier | Table Power BI |
|---|---|
| `dim_date.parquet` | `Dim_Date` |
| `dim_sous_secteur.parquet` | `Dim_Sous_Secteur` |
