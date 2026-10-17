# Connecteurs de sources

Un module par source (`eurostat.py`, `insee.py`, `aft.py`…), ajoutés à partir du lot 1.

Chaque connecteur :

1. télécharge les fichiers **sans aucune transformation métier** ;
2. les archive dans un instantané avec `ingestion.common.archivage.Instantane` ;
3. renseigne la date de publication du producteur quand elle est connue.

Les transformations ont lieu dans `transform/` (dbt).
