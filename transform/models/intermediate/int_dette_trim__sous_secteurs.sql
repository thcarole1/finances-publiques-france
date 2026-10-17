-- Dette trimestrielle (Eurostat) par pays, trimestre et secteur, en M€ et monnaie nationale.
select
    geo, annee, periode, sector,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(coalesce(flag, ''), '')               as flags
from {{ ref('stg_eurostat__gov_10q_ggdebt') }}
where unit in ('MIO_EUR', 'MIO_NAC') and valeur is not null
group by all
