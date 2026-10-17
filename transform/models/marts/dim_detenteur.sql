-- Dim_Detenteur : à qui les administrations doivent leur dette.
select
    cast(detenteur_code as varchar) as detenteur_code,
    cast(libelle as varchar)        as libelle,
    cast(groupe as varchar)         as groupe,
    cast(definition as varchar)     as definition,
    cast(ordre_tri as integer)      as ordre_tri
from {{ ref('ref_detenteur') }}
