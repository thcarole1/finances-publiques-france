-- Dim_Agregat_Trimestriel : agrégats des comptes trimestriels des administrations publiques.
select
    cast(agregat_code as varchar) as agregat_code,
    cast(libelle as varchar)      as libelle,
    cast(ordre_tri as integer)    as ordre_tri
from {{ ref('ref_agregat_trimestriel') }}
