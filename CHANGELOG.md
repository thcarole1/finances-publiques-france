# Journal des évolutions

Format : une section par version ; une version mineure par lot livré (docs/10-conventions.md).

## [0.3.0] — lot 1b : qui paie ?

### Ajouté
- Connecteur DG TAXUD (listes nationales des impôts, base économique de chaque impôt).
- Répartition des prélèvements par base économique et par payeur (`Fait_Prelevements_Fonction`),
  lectures légale et économique (`Dim_Fonction_Economique`), avec origine de chaque répartition.
- Contrôle QC-B09 (conservation des montants) et contrôle de double compte des listes nationales.
- Power BI : mesures « Prélèvements par payeur » et « Part » ; colonnes Payeur (légal / économique).
- Note de lot `docs/lots/lot-1b.md` (vérification contre les fiches pays de la Commission).

## [0.2.0] — lot 1 : socle Eurostat

### Ajouté
- Connecteur Eurostat (5 jeux, UE27 + agrégats + Norvège + Suisse, depuis 1995).
- Archivage des données brutes dans les Releases GitHub et récupération automatique.
- Workflow `collecte` complet : collecte, contrôles, archivage, pull request de données.
- Référentiels : pays, natures (SEC 2010), fonctions (COFOG), prélèvements, sources, indicateurs.
- Faits F01 à F05 avec consolidation par écritures d'élimination et résidus « non ventilé ».
- Contrôles qualité QC-B03, B04, B05, B10, B12 (bloquants), QC-A01, A03, A04 (avertissements).
- Modèle Power BI : 15 nouvelles tables, relations, mesures, groupes de calcul unité et consolidation.
- Validation du TMDL en CI avec la bibliothèque Microsoft (job `modele-powerbi`).
- Note de lot `docs/lots/lot-1.md` (vérification contre l'INSEE, choix, reports).

## [0.1.0] — lot 0 (en cours)

### Ajouté
- Spécification v1.0 (`docs/`) et décisions D1 à D11.
- Outillage Python (`uv`, `ruff`, `pytest`) et projet **dbt-duckdb** (`transform/`).
- Archivage des instantanés bruts avec manifeste et empreintes (`ingestion/common/archivage.py`).
- Premières tables du modèle : `Dim_Date` (1990–2075) et `Dim_Sous_Secteur`, avec contrats et tests.
- Format et validation des scénarios personnels (`scenarios/`, QC-B11).
- Intégration continue (`ci.yml`) et squelette du workflow de collecte (`collecte.yml`).
- Mode d'emploi du projet Power BI (`powerbi/README.md`).
