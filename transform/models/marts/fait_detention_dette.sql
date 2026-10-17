-- F10 — Fait_Detention_Dette : dette consolidée de l'ensemble des administrations en fin
-- d'année, par détenteur (investisseurs étrangers, banque centrale, banques…). Semi-additive.
-- Eurostat ne publie le détail que depuis 2020 pour la plupart des pays.
with millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10dd_ggd' and est_dernier
)
select
    p.pays_code,
    d.annee * 10000 + 1231                         as date_id,
    d.detenteur_code,
    round(d.valeur_meur, 3)                        as valeur_meur,
    round(d.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('d.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10DD_GGD'                        as source_id,
    (select millesime_id from millesime)           as millesime_id
from {{ ref('int_dette__detenteurs') }} as d
join {{ ref('ref_pays') }} as p on p.code_eurostat = d.geo
