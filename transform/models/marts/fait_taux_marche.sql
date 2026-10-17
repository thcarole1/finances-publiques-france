-- F12 — Fait_Taux_Marche : taux des emprunts d'État à 10 ans, moyenne du mois, daté du dernier
-- jour du mois. Non additive (mesures Power BI en moyenne).
with millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'irt_lt_mcby_m' and est_dernier
)
select
    p.pays_code,
    cast(strftime(last_day(strptime(t.periode || '-01', '%Y-%m-%d')), '%Y%m%d') as integer)
                                                   as date_id,
    '10 ans'                                       as maturite,
    round(t.valeur, 4)                             as taux_pct,
    {{ statut_valeur("coalesce(t.flag, '')") }}    as statut_valeur,
    'EUROSTAT_IRT_LT_MCBY_M'                       as source_id,
    (select millesime_id from millesime)           as millesime_id
from {{ ref('stg_eurostat__irt_lt_mcby_m') }} as t
join {{ ref('ref_pays') }} as p on p.code_eurostat = t.geo
