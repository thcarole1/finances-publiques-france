-- Dim_Instrument_Dette : sous quelle forme les administrations empruntent.
select
    cast(instrument_code as varchar) as instrument_code,
    cast(libelle as varchar)         as libelle,
    cast(libelle_court as varchar)   as libelle_court,
    cast(famille as varchar)         as famille,
    cast(duree_origine as varchar)   as duree_origine,
    cast(definition as varchar)      as definition,
    cast(ordre_tri as integer)       as ordre_tri
from {{ ref('ref_instrument_dette') }}
