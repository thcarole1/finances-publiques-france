-- F04 — Fait_Macro_Annuel : dénominateurs (PIB, population) et contexte (croissance, prix).
with pib as (
    select geo, annee,
        max(case when unit = 'CP_MEUR' then valeur end)          as pib_meur,
        max(case when unit = 'CP_MNAC' then valeur end)          as pib_mnac,
        max(case when unit = 'CLV_PCH_PRE' then valeur end)      as croissance_volume_pct,
        max(case when unit = 'PD_PCH_PRE_EUR' then valeur end)   as variation_deflateur_pct,
        string_agg(coalesce(flag, ''), '')                       as flags
    from {{ ref('stg_eurostat__nama_10_gdp') }}
    where na_item = 'B1GQ'
    group by all
),
pop as (
    select geo, annee, valeur * 1000 as population
    from {{ ref('stg_eurostat__nama_10_pe') }}
    where unit = 'THS_PER' and na_item = 'POP_NC'
)
select
    p.pays_code,
    coalesce(pib.annee, pop.annee) * 10000 + 1231  as date_id,
    pib.pib_meur,
    pib.pib_mnac,
    pib.croissance_volume_pct,
    pib.variation_deflateur_pct,
    cast(round(pop.population) as bigint)          as population,
    {{ statut_valeur('pib.flags') }}               as statut_valeur,
    'EUROSTAT_NAMA_10_GDP'                         as source_id
from pib
full join pop using (geo, annee)
join {{ ref('ref_pays') }} as p on p.code_eurostat = coalesce(pib.geo, pop.geo)
