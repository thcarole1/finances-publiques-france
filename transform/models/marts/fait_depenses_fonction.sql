-- F02 — Fait_Depenses_Fonction : COFOG (feuilles) × nature × sous-secteur, avec S13_ELIM.
with feuilles as (select * from {{ ref('int_depenses_fonction__feuilles') }}),
consolide as (
    {{ consolider_sous_secteurs("feuilles", ["geo", "annee", "cofog", "transaction_code"]) }}
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10a_exp' and est_dernier
)
select
    p.pays_code,
    c.annee * 10000 + 1231                         as date_id,
    c.sector                                       as sous_secteur_code,
    c.cofog                                        as cofog_code,
    c.transaction_code,
    round(c.valeur_meur, 3)                        as valeur_meur,
    round(c.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('c.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10A_EXP'                         as source_id,
    (select millesime_id from millesime)           as millesime_id
from consolide as c
join {{ ref('ref_pays') }} as p on p.code_eurostat = c.geo
