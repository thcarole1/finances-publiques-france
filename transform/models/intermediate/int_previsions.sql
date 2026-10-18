-- Prévisions de la Commission (AMECO), du FMI et du gouvernement (France), harmonisées : une ligne par institution ×
-- édition × pays × année cible × variable, valeur en % (du PIB ou de croissance).
with variables as (select * from {{ ref('ref_variable_prevision') }}),
pays as (select pays_code, code_iso3 from {{ ref('ref_pays') }} where code_iso3 is not null and code_iso3 <> ''),

ameco_niveaux as (
    select a.edition, a.zone, a.annee, v.variable_code, a.valeur
    from {{ ref('stg_commission__ameco') }} as a
    join variables as v on v.code_ameco = a.variable
    where a.code like '%.1.0.319.0.%' or a.code like '%.1.1.0.0.OVGD'
),
ameco as (
    -- Croissance : variation du PIB en volume d'une année sur l'autre, dans la même édition.
    select edition, zone, annee, variable_code,
        case when variable_code = 'CROISSANCE'
            then (valeur / lag(valeur) over (partition by edition, zone, variable_code order by annee) - 1) * 100
            else valeur end as valeur
    from ameco_niveaux
),
fmi as (
    select f.edition, f.zone, f.annee, v.variable_code, f.valeur
    from {{ ref('stg_fmi__weo') }} as f
    join variables as v on v.code_fmi = f.variable
),
gouvernement as (
    select edition, 'FRA' as zone, annee, variable_code, valeur
    from {{ ref('ref_previsions_gouvernement') }}
),
toutes as (
    select 'COMMISSION' as institution, * from ameco
    union all
    select 'FMI' as institution, * from fmi
    union all
    select 'GOUVERNEMENT' as institution, * from gouvernement
)
select
    t.institution,
    t.institution || '_' || t.edition                         as edition_id,
    t.edition,
    cast(left(t.edition, 4) as integer)                       as annee_publication,
    p.pays_code,
    t.annee                                                   as annee_cible,
    t.variable_code,
    t.valeur
from toutes as t
join pays as p on p.code_iso3 = t.zone
where t.valeur is not null
    and t.annee between cast(left(t.edition, 4) as integer) - 1 and cast(left(t.edition, 4) as integer) + 5
