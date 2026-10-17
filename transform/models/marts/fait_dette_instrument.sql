-- F09b — Fait_Dette_Instrument : dette consolidée de l'ensemble des administrations en fin
-- d'année, par instrument (obligations, titres de court terme, prêts, dépôts). Semi-additive.
with millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10dd_edpt1' and est_dernier
)
select
    p.pays_code,
    i.annee * 10000 + 1231                         as date_id,
    i.instrument_code,
    round(i.valeur_meur, 3)                        as valeur_meur,
    round(i.valeur_mnac, 3)                        as valeur_mnac,
    {{ statut_valeur('i.flags') }}                 as statut_valeur,
    'EUROSTAT_GOV_10DD_EDPT1'                      as source_id,
    (select millesime_id from millesime)           as millesime_id
from {{ ref('int_dette__instruments') }} as i
join {{ ref('ref_pays') }} as p on p.code_eurostat = i.geo
