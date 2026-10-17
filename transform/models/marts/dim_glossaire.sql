-- Dim_Glossaire : définitions affichées dans le rapport (page Glossaire, encadrés « Comprendre »).
-- Source unique : docs/glossaire.md (→ data/reference/ref_glossaire.csv, scripts/generer_glossaire.py).
select
    cast(glossaire_id as varchar)      as glossaire_id,
    cast(terme as varchar)             as terme,
    cast(definition_courte as varchar) as definition_courte,
    cast(definition_longue as varchar) as definition_longue,
    cast(ordre_tri as integer)         as ordre_tri
from {{ ref('ref_glossaire') }}
