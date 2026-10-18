-- Dim_Variable_Prevision : variables suivies dans les prévisions.
select
    cast(variable_code as varchar)  as variable_code,
    cast(libelle as varchar)        as libelle,
    cast(unite as varchar)          as unite,
    cast(sens_optimisme as integer) as sens_optimisme,
    cast(definition as varchar)     as definition,
    cast(ordre_tri as integer)      as ordre_tri
from {{ ref('ref_variable_prevision') }}
