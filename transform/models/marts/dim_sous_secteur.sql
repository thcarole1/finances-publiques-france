-- Dim_Sous_Secteur : sous-secteurs des APU, y compris la ligne d'élimination S13_ELIM.
select
    sous_secteur_code,
    libelle,
    libelle_court,
    niveau,
    parent_code,
    est_elimination,
    ordre_tri,
    definition_courte
from {{ ref('ref_sous_secteur') }}
