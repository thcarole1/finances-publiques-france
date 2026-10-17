-- F09c — Fait_Dette_Contributions (France) : contribution de chaque administration à la dette
-- consolidée, en fin de trimestre (INSEE). Détaille l'administration centrale en État et
-- organismes (agences, universités…). Σ contributions = dette totale (QC-B14). Semi-additive.
with s as (
    select b.*, r.code as sous_secteur_code
    from {{ ref('stg_insee__bdm') }} as b
    join {{ ref('ref_series_insee') }} as r on r.idbank = b.idbank
    where r.usage = 'dette_contribution' and b.valeur_m is not null
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where source = 'insee' and jeu = 'dette-trim-apu' and est_dernier
)
select
    'FR'                                           as pays_code,
    {{ fin_de_periode('s.periode') }}              as date_id,
    s.sous_secteur_code,
    round(s.valeur_m, 3)                           as valeur_meur,
    case when s.statut = 'DEF' then 'DEFINITIF' else 'PROVISOIRE' end as statut_valeur,
    'INSEE_DETTE-TRIM-APU'                         as source_id,
    (select millesime_id from millesime)           as millesime_id
from s
