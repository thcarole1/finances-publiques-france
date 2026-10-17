-- F08 — Fait_Macro_Trimestriel : PIB trimestriel à prix courants, brut et corrigé des variations
-- saisonnières (CVS). pib_4t_meur = somme des quatre derniers trimestres (dénominateur du ratio
-- de dette trimestriel, comme Eurostat). Non additive.
with obs as (
    select geo, annee, periode,
        case s_adj when 'NSA' then 'BRUT' when 'SCA' then 'CVS' end as correction,
        max(case when unit = 'CP_MEUR' then valeur end)              as pib_meur,
        max(case when unit = 'CP_MNAC' then valeur end)              as pib_mnac,
        string_agg(coalesce(flag, ''), '')                           as flags
    from {{ ref('stg_eurostat__namq_10_gdp') }}
    where s_adj in ('NSA', 'SCA') and valeur is not null
    group by all
),
glissant as (
    select *,
        sum(pib_meur) over w4                 as somme_4t,
        count(pib_meur) over w4               as nb_4t
    from obs
    window w4 as (partition by geo, correction order by periode rows between 3 preceding and current row)
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'namq_10_gdp' and est_dernier
)
select
    p.pays_code,
    {{ fin_de_periode('g.periode') }}                      as date_id,
    g.correction,
    round(g.pib_meur, 3)                                   as pib_meur,
    round(g.pib_mnac, 3)                                   as pib_mnac,
    round(case when g.nb_4t = 4 then g.somme_4t end, 3)    as pib_4t_meur,
    {{ statut_valeur('g.flags') }}                         as statut_valeur,
    'EUROSTAT_NAMQ_10_GDP'                                 as source_id,
    (select millesime_id from millesime)                   as millesime_id
from glissant as g
join {{ ref('ref_pays') }} as p on p.code_eurostat = g.geo
