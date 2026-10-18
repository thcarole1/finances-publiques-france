-- F13 — Fait_Previsions : prévisions (Commission, FMI) par édition × pays × année cible ×
-- variable, rapprochées de la valeur réalisée ; plus les lignes « Réalité » (édition REALITE)
-- pour le graphique en spaghetti. Non additive.
--   ecart            = prévu − réalisé (en points) ;
--   ecart_optimisme  = écart orienté : positif si la prévision était trop optimiste
--                      (solde ou croissance trop hauts, dette trop basse).
with p as (select * from {{ ref('int_previsions') }}),
r as (select * from {{ ref('int_previsions__realise') }}),
v as (select variable_code, sens_optimisme from {{ ref('ref_variable_prevision') }}),
annees_previsions as (select distinct pays_code, variable_code from p)
select
    p.edition_id,
    p.pays_code,
    cast(p.annee_cible * 10000 + 1231 as integer)                   as date_id,
    p.variable_code,
    round(p.valeur, 4)                                             as valeur,
    cast(p.annee_cible - p.annee_publication as integer)           as horizon,
    case p.annee_cible - p.annee_publication
        when -1 then 'Année écoulée' when 0 then 'Année en cours' when 1 then 'Année suivante'
        else 'Dans ' || (p.annee_cible - p.annee_publication) || ' ans' end as libelle_horizon,
    round(r.valeur, 4)                                             as realise,
    round(p.valeur - r.valeur, 4)                                  as ecart,
    round((p.valeur - r.valeur) * v.sens_optimisme, 4)             as ecart_optimisme,
    case p.institution when 'COMMISSION' then 'COMMISSION_AMECO' when 'FMI' then 'FMI_WEO'
        else 'GOUVERNEMENT_TRAJECTOIRES' end                       as source_id
from p
join v using (variable_code)
left join r on r.pays_code = p.pays_code and r.annee = p.annee_cible and r.variable_code = p.variable_code
union all
select
    'REALITE', r.pays_code, cast(r.annee * 10000 + 1231 as integer), r.variable_code, round(r.valeur, 4),
    null, null, round(r.valeur, 4), null, null, 'EUROSTAT_GOV_10A_MAIN'
from r
join annees_previsions as a using (pays_code, variable_code)
where r.annee >= 2008
