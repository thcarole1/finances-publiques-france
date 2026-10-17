-- Feuilles de prélèvements : impôts et cotisations détaillés, avec résidus « non ventilé »
-- à chaque niveau de la hiérarchie (ref_formule_prelevement), Σ feuilles = total publié.
with obs as (
    select geo, annee, sector, unit, na_item, valeur, flag
    from {{ ref('stg_eurostat__gov_10a_taxag') }}
),
ancres as (
    select distinct geo, annee, sector, unit
    from obs where na_item = 'D2_D5_D91_D61_M_D995' and valeur is not null
),
calcul as (
    select
        a.geo, a.annee, a.sector, a.unit, f.prelevement_code,
        sum(f.coefficient * coalesce(o.valeur, 0)) as valeur,
        count(o.valeur)                            as nb_composantes,
        string_agg(coalesce(o.flag, ''), '')       as flags
    from ancres as a
    cross join {{ ref('ref_formule_prelevement') }} as f
    left join obs as o
        on o.geo = a.geo and o.annee = a.annee and o.sector = a.sector
        and o.unit = a.unit and o.na_item = f.na_item
    group by all
)
select
    geo, annee, sector, prelevement_code,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(flags, '')                            as flags
from calcul
where nb_composantes > 0
group by all
