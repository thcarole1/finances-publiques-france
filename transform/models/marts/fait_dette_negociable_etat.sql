-- F11a — Fait_Dette_Negociable_Etat (France) : encours de la dette négociable de l'État en fin
-- de mois, selon deux axes (durée ; type de taux). Additive à axe fixé, jamais entre axes ni
-- dans le temps (QC-B15 : chaque axe redonne l'encours total).
with s as (
    select b.*, r.code as composante_code
    from {{ ref('stg_insee__bdm') }} as b
    join {{ ref('ref_series_insee') }} as r on r.idbank = b.idbank
    where r.usage = 'dette_negociable' and b.valeur_m is not null
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where source = 'insee' and jeu = 'dette-negociable-etat' and est_dernier
)
select
    'FR'                                           as pays_code,
    {{ fin_de_periode('s.periode') }}              as date_id,
    s.composante_code,
    round(s.valeur_m, 3)                           as valeur_meur,
    'DEFINITIF'                                    as statut_valeur,
    'INSEE_DETTE-NEGOCIABLE-ETAT'                  as source_id,
    (select millesime_id from millesime)           as millesime_id
from s
