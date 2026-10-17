-- F09 — Fait_Dette : dette publique (au sens de Maastricht) en fin d'année, par sous-secteur,
-- avec la ligne S13_ELIM qui retire les dettes entre administrations (Σ lignes = dette S13).
-- Semi-additive : ne pas additionner dans le temps (mesures Power BI à la dernière date).
with base as (select * from {{ ref('int_dette__sous_secteurs') }}),
consolide as (
    {{ consolider_sous_secteurs("base", ["geo", "annee"]) }}
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10dd_edpt1' and est_dernier
)
select
    p.pays_code,
    c.annee * 10000 + 1231                         as date_id,
    c.sector                                       as sous_secteur_code,
    round(c.valeur_meur, 3)                        as valeur_meur,
    round(c.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('c.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10DD_EDPT1'                      as source_id,
    (select millesime_id from millesime)           as millesime_id
from consolide as c
join {{ ref('ref_pays') }} as p on p.code_eurostat = c.geo
