# Journal des évolutions

Format : une section par version ; une version mineure par lot livré (docs/10-conventions.md).

## [0.1.0] — lot 0 (en cours)

### Ajouté
- Spécification v1.0 (`docs/`) et décisions D1 à D11.
- Outillage Python (`uv`, `ruff`, `pytest`) et projet **dbt-duckdb** (`transform/`).
- Archivage des instantanés bruts avec manifeste et empreintes (`ingestion/common/archivage.py`).
- Premières tables du modèle : `Dim_Date` (1990–2075) et `Dim_Sous_Secteur`, avec contrats et tests.
- Format et validation des scénarios personnels (`scenarios/`, QC-B11).
- Intégration continue (`ci.yml`) et squelette du workflow de collecte (`collecte.yml`).
- Mode d'emploi du projet Power BI (`powerbi/README.md`).
