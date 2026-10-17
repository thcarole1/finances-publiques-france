-- F03 — Fait_Prelevements : impôts et cotisations par sous-secteur bénéficiaire, avec S13_ELIM.
with feuilles as (select * from {{ ref('int_prelevements__feuilles') }}),
consolide as (
    {{ consolider_sous_secteurs("feuilles", ["geo", "annee", "prelevement_code"]) }}
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10a_taxag' and est_dernier
)
select
    p.pays_code,
    c.annee * 10000 + 1231                         as date_id,
    c.sector                                       as sous_secteur_code,
    c.prelevement_code,
    round(c.valeur_meur, 3)                        as valeur_meur,
    round(c.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('c.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10A_TAXAG'                       as source_id,
    (select millesime_id from millesime)           as millesime_id
from consolide as c
join {{ ref('ref_pays') }} as p on p.code_eurostat = c.geo
