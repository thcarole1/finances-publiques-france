-- F06 — Fait_Transferts_APU : qui finance qui, entre administrations publiques.
-- Source : postes « dont au sous-secteur … » de gov_10a_main (Eurostat), versés par chaque
-- sous-secteur à chaque autre : revenus de la propriété (D4), autres transferts courants (D7,
-- dont dotations), transferts en capital (D9, dont aides à l'investissement).
-- Les flux internes à un sous-secteur sont déjà consolidés par le producteur (non publiés).
with obs as (
    select geo, annee, sector as versant,
        regexp_extract(na_item, '^(D[479])PAY_(S131[1-4])$', 1) as operation,
        regexp_extract(na_item, '^(D[479])PAY_(S131[1-4])$', 2) as receveur,
        unit, valeur, flag
    from {{ ref('stg_eurostat__gov_10a_main') }}
    where regexp_matches(na_item, '^D[479]PAY_S131[1-4]$')
        and sector in ('S1311', 'S1312', 'S1313', 'S1314')
        and valeur is not null
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where jeu = 'gov_10a_main' and est_dernier
)
select
    p.pays_code,
    o.annee * 10000 + 1231                                       as date_id,
    o.versant                                                    as sous_secteur_versant_code,
    o.receveur                                                   as sous_secteur_receveur_code,
    o.operation || '_PAY'                                        as transaction_code,
    round(max(case when o.unit = 'MIO_EUR' then o.valeur end), 3) as valeur_meur,
    round(max(case when o.unit = 'MIO_NAC' then o.valeur end), 3) as valeur_mnac,
    {{ statut_valeur("string_agg(coalesce(o.flag, ''), '')") }}  as statut_valeur,
    'EUROSTAT_GOV_10A_MAIN'                                      as source_id,
    (select millesime_id from millesime)                         as millesime_id
from obs as o
join {{ ref('ref_pays') }} as p on p.code_eurostat = o.geo
where o.versant <> o.receveur
group by all
having abs(coalesce(max(case when o.unit = 'MIO_EUR' then o.valeur end), 0)) > 0.05
