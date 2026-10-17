-- F01 — Fait_Comptes_APU_Annuels : feuilles de recettes et de dépenses par sous-secteur,
-- avec la ligne d'élimination S13_ELIM (Σ toutes lignes = S13 consolidé).
with feuilles as (select * from {{ ref('int_comptes_apu__feuilles') }}),
consolide as (
    {{ consolider_sous_secteurs("feuilles", ["geo", "annee", "transaction_code"]) }}
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10a_main' and est_dernier
)
select
    p.pays_code,
    c.annee * 10000 + 1231                         as date_id,
    c.sector                                       as sous_secteur_code,
    c.transaction_code,
    round(c.valeur_meur, 3)                        as valeur_meur,
    round(c.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('c.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10A_MAIN'                        as source_id,
    (select millesime_id from millesime)           as millesime_id
from consolide as c
join {{ ref('ref_pays') }} as p on p.code_eurostat = c.geo
