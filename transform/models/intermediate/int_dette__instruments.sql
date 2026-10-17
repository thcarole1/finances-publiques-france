-- Dette consolidée de l'ensemble des administrations (S13) répartie par instrument.
-- Feuilles exhaustives : la feuille GD_NV est le résidu qui garantit Σ feuilles = GD publié.
with obs as (
    select geo, annee, unit, na_item, valeur, flag
    from {{ ref('stg_eurostat__gov_10dd_edpt1') }}
    where sector = 'S13' and valeur is not null
),
total as (select * from obs where na_item = 'GD'),
feuilles as (
    select o.geo, o.annee, o.unit, i.instrument_code, o.valeur, o.flag
    from obs as o
    join {{ ref('ref_instrument_dette') }} as i on i.na_item = o.na_item
),
residu as (
    select t.geo, t.annee, t.unit, 'GD_NV' as instrument_code,
        t.valeur - coalesce(sum(f.valeur), 0) as valeur, t.flag
    from total as t
    left join feuilles as f using (geo, annee, unit)
    group by t.geo, t.annee, t.unit, t.valeur, t.flag
),
toutes as (
    select * from feuilles
    union all
    select * from residu where abs(valeur) > 1
)
select
    geo, annee, instrument_code,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(coalesce(flag, ''), '')               as flags
from toutes
group by all
