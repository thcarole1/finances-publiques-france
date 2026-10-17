-- Dette consolidée des administrations (S13) répartie par détenteur. Feuilles exhaustives :
--   S1_NV = résidents (S1) − Σ catégories de résidents détaillées ;
--   NV    = total (S1_S2) − résidents (S1) − non-résidents (S2).
with obs as (
    select geo, annee, unit, sector2, valeur, flag
    from {{ ref('stg_eurostat__gov_10dd_ggd') }}
    where valeur is not null
),
synthese as (
    select geo, annee, unit,
        max(valeur) filter (where sector2 = 'S1_S2') as total,
        max(valeur) filter (where sector2 = 'S1')    as residents,
        max(valeur) filter (where sector2 = 'S2')    as non_residents,
        string_agg(coalesce(flag, ''), '')           as flags
    from obs
    group by all
),
detail as (
    select o.geo, o.annee, o.unit, d.detenteur_code, o.valeur
    from obs as o
    join {{ ref('ref_detenteur') }} as d on d.sector2 = o.sector2
),
residus as (
    select p.geo, p.annee, p.unit, 'S1_NV' as detenteur_code,
        p.residents - coalesce(sum(d.valeur) filter (where d.detenteur_code <> 'S2'), 0) as valeur
    from synthese as p
    left join detail as d using (geo, annee, unit)
    where p.residents is not null
    group by p.geo, p.annee, p.unit, p.residents
    union all
    select geo, annee, unit, 'NV',
        total - coalesce(residents, 0) - coalesce(non_residents, 0)
    from synthese
    where total is not null
),
toutes as (
    select * from detail
    union all
    select * from residus where abs(valeur) > 1
)
select
    t.geo, t.annee, t.detenteur_code,
    max(case when t.unit = 'MIO_EUR' then t.valeur end) as valeur_meur,
    max(case when t.unit = 'MIO_NAC' then t.valeur end) as valeur_mnac,
    max(p.flags)                                        as flags
from toutes as t
join synthese as p using (geo, annee, unit)
group by t.geo, t.annee, t.detenteur_code
