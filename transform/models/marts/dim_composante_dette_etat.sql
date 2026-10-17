-- Dim_Composante_Dette_Etat : composantes de la dette négociable de l'État (deux axes).
select
    cast(composante_code as varchar) as composante_code,
    cast(libelle as varchar)         as libelle,
    cast(axe as varchar)             as axe,
    cast(definition as varchar)      as definition,
    cast(ordre_tri as integer)       as ordre_tri
from {{ ref('ref_composante_dette_etat') }}
