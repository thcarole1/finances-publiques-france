-- F09t — Fait_Dette_Trimestrielle : dette de Maastricht en fin de trimestre par sous-secteur,
-- avec la ligne S13_ELIM (Σ lignes = dette S13). Semi-additive. Le T4 doit égaler la dette
-- annuelle de Fait_Dette (QC-B06, avertissement : les deux jeux ne sont pas publiés le même jour).
with base as (select * from {{ ref('int_dette_trim__sous_secteurs') }}),
consolide as (
    {{ consolider_sous_secteurs("base", ["geo", "annee", "periode"]) }}
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10q_ggdebt' and est_dernier
)
select
    p.pays_code,
    {{ fin_de_periode('c.periode') }}              as date_id,
    c.sector                                       as sous_secteur_code,
    round(c.valeur_meur, 3)                        as valeur_meur,
    round(c.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('c.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10Q_GGDEBT'                      as source_id,
    (select millesime_id from millesime)           as millesime_id
from consolide as c
join {{ ref('ref_pays') }} as p on p.code_eurostat = c.geo
