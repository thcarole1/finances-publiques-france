-- F07 — Fait_Comptes_APU_Trimestriels : dépenses, recettes, solde et intérêts de l'ensemble des
-- administrations (S13) par trimestre, bruts et CVS. Additive dans le temps à correction fixée
-- (ne jamais mélanger BRUT et CVS) ; le solde n'est pas la somme des autres agrégats.
with obs as (
    select o.geo, o.periode,
        case o.s_adj when 'NSA' then 'BRUT' when 'SCA' then 'CVS' end as correction,
        a.agregat_code,
        max(case when o.unit = 'MIO_EUR' then o.valeur end)            as valeur_meur,
        max(case when o.unit = 'MIO_NAC' then o.valeur end)            as valeur_mnac,
        string_agg(coalesce(o.flag, ''), '')                           as flags
    from {{ ref('stg_eurostat__gov_10q_ggnfa') }} as o
    join {{ ref('ref_agregat_trimestriel') }} as a on a.na_item = o.na_item
    where o.s_adj in ('NSA', 'SCA') and o.unit in ('MIO_EUR', 'MIO_NAC') and o.valeur is not null
    group by all
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10q_ggnfa' and est_dernier
)
select
    p.pays_code,
    {{ fin_de_periode('o.periode') }}              as date_id,
    o.correction,
    o.agregat_code,
    round(o.valeur_meur, 3)                        as valeur_meur,
    round(o.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('o.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10Q_GGNFA'                       as source_id,
    (select millesime_id from millesime)           as millesime_id
from obs as o
join {{ ref('ref_pays') }} as p on p.code_eurostat = o.geo
