# Tables du modèle (Parquet)

Produites par `./scripts/construire.sh` (dbt) — **ne pas modifier à la main**. Dans le dépôt,
elles sont mises à jour par le workflow `collecte` à partir des données brutes archivées.
Un fichier par table du modèle Power BI ; les lignes sont triées pour que deux constructions
identiques produisent des fichiers identiques.

| Fichier | Table Power BI |
|---|---|
| `dim_date.parquet` | `Dim_Date` |
| `dim_sous_secteur.parquet` | `Dim_Sous_Secteur` |
| `dim_pays.parquet` | `Dim_Pays` |
| `dim_transaction.parquet` | `Dim_Transaction` |
| `dim_cofog.parquet` | `Dim_COFOG` |
| `dim_prelevement.parquet` | `Dim_Prelevement` |
| `dim_source.parquet` | `Dim_Source` |
| `dim_glossaire.parquet` | `Dim_Glossaire` |
| `dim_instrument_dette.parquet` | `Dim_Instrument_Dette` |
| `dim_detenteur.parquet` | `Dim_Detenteur` |
| `fait_dette.parquet` | `Fait_Dette` |
| `fait_dette_instrument.parquet` | `Fait_Dette_Instrument` |
| `fait_detention_dette.parquet` | `Fait_Detention_Dette` |
| `fait_taux_marche.parquet` | `Fait_Taux_Marche` |
| `dim_millesime.parquet` | `Dim_Millesime` |
| `dim_indicateur.parquet` | `Dim_Indicateur` |
| `fait_comptes_apu_annuels.parquet` | `Fait_Comptes_APU_Annuels` (F01) |
| `fait_depenses_fonction.parquet` | `Fait_Depenses_Fonction` (F02) |
| `fait_prelevements.parquet` | `Fait_Prelevements` (F03) |
| `fait_prelevements_fonction.parquet` | `Fait_Prelevements_Fonction` (F03b) |
| `dim_fonction_economique.parquet` | `Dim_Fonction_Economique` |
| `fait_macro_annuel.parquet` | `Fait_Macro_Annuel` (F04) |
| `fait_revisions.parquet` | `Fait_Revisions` (F05) |
