-- Fait_Prelevements_Fonction : les prélèvements (F03) répartis par base économique (DG TAXUD).
-- Σ sur les bases = F03, ligne à ligne. Le type de part indique d'où vient la répartition :
--   NTL         : liste nationale du pays, pour l'année ;
--   PROLONGEE   : liste nationale du pays, année la plus proche (année non encore couverte) ;
--   MOYENNE_UE  : pas de base publiée pour ce prélèvement dans ce pays : composition moyenne des
--                 pays européens pour le même prélèvement et la même année (pondérée par les montants) ;
--   AGREGAT     : UE27 / zone euro, composition des pays membres ;
--   DEFAUT      : prélèvement absent des listes, rattachement documenté (ref_fonction_defaut) ;
--   NV          : aucune information (montant entier en « non ventilé »).
with f03 as (
    select f.*, p.code_eurostat as geo, f.date_id // 10000 as annee, p.type as type_pays
    from {{ ref('fait_prelevements') }} as f
    join {{ ref('dim_pays') }} as p using (pays_code)
),
parts as (select * from {{ ref('int_prelevements__parts_fonction') }}),
annees_parts as (select distinct geo, prelevement_code, annee from parts),
cles_pays as (
    select distinct pays_code, geo, annee, date_id, prelevement_code
    from f03 where type_pays = 'Pays'
),
annee_source as (
    -- Année de la liste nationale à utiliser : l'année même, sinon la plus proche avant, sinon après.
    select k.pays_code, k.date_id, k.prelevement_code, k.geo, k.annee,
        coalesce(
            (select max(a.annee) from annees_parts as a
             where a.geo = k.geo and a.prelevement_code = k.prelevement_code and a.annee <= k.annee),
            (select min(a.annee) from annees_parts as a
             where a.geo = k.geo and a.prelevement_code = k.prelevement_code)
        ) as annee_parts
    from cles_pays as k
),
parts_pays as (
    select s.pays_code, s.date_id, s.prelevement_code, p.fonction_code, p.part,
        case when s.annee_parts = s.annee then 'NTL' else 'PROLONGEE' end as type_part
    from annee_source as s
    join parts as p
        on p.geo = s.geo and p.prelevement_code = s.prelevement_code and p.annee = s.annee_parts
),
totaux_pays as (
    select pays_code, date_id, prelevement_code, sum(valeur_meur) as valeur
    from f03 where type_pays = 'Pays' group by all
),
moyenne_ue as (
    -- Composition moyenne des pays de l'UE couverts, pondérée par leurs montants (en valeur
    -- absolue : les feuilles résiduelles peuvent être de signe variable).
    select pp.date_id, pp.prelevement_code, pp.fonction_code,
        sum(abs(t.valeur) * pp.part) as valeur
    from parts_pays as pp
    join totaux_pays as t using (pays_code, date_id, prelevement_code)
    join {{ ref('dim_pays') }} as d using (pays_code)
    where d.est_ue
    group by all
),
moyenne_ue_parts as (
    select date_id, prelevement_code, fonction_code,
        valeur / sum(valeur) over (partition by date_id, prelevement_code) as part
    from moyenne_ue
    qualify sum(valeur) over (partition by date_id, prelevement_code) > 0
),
parts_pays_completes as (
    select * from parts_pays
    union all
    select k.pays_code, k.date_id, k.prelevement_code, m.fonction_code, m.part, 'MOYENNE_UE'
    from (select distinct pays_code, date_id, prelevement_code from cles_pays) as k
    join moyenne_ue_parts as m using (date_id, prelevement_code)
    anti join (select distinct pays_code, date_id, prelevement_code from parts_pays) as d
        using (pays_code, date_id, prelevement_code)
),
membres as (
    select 'EU27' as agregat, pays_code from {{ ref('dim_pays') }} where type = 'Pays' and est_ue
    union all
    select 'EA', pays_code from {{ ref('dim_pays') }} where type = 'Pays' and est_zone_euro
),
montants_agregats as (
    select m.agregat as pays_code, pp.date_id, pp.prelevement_code, pp.fonction_code,
        sum(abs(t.valeur) * pp.part) as valeur
    from parts_pays_completes as pp
    join totaux_pays as t using (pays_code, date_id, prelevement_code)
    join membres as m using (pays_code)
    group by m.agregat, pp.date_id, pp.prelevement_code, pp.fonction_code
),
parts_agregats as (
    select pays_code, date_id, prelevement_code, fonction_code,
        valeur / sum(valeur) over (partition by pays_code, date_id, prelevement_code) as part,
        'AGREGAT' as type_part
    from montants_agregats
    qualify sum(valeur) over (partition by pays_code, date_id, prelevement_code) > 0
),
toutes_parts as (
    select * from parts_pays_completes
    union all
    select * from parts_agregats
),
reparti as (
    select f.pays_code, f.date_id, f.sous_secteur_code, f.prelevement_code,
        coalesce(t.fonction_code, d.fonction_code, 'NV') as fonction_code,
        coalesce(t.part, 1.0) as part,
        coalesce(t.type_part, case when d.fonction_code is null then 'NV' else 'DEFAUT' end) as type_part
    from f03 as f
    left join toutes_parts as t using (pays_code, date_id, prelevement_code)
    left join {{ ref('ref_fonction_defaut') }} as d
        on d.prelevement_code = f.prelevement_code and t.fonction_code is null
)
select
    r.pays_code, r.date_id, r.sous_secteur_code, r.prelevement_code, r.fonction_code,
    round(f.valeur_meur * r.part, 3)    as valeur_meur,
    round(f.valeur_mnac * r.part, 3)    as valeur_mnac,
    r.type_part,
    f.statut_valeur,
    f.source_id,
    f.millesime_id
from reparti as r
join {{ ref('fait_prelevements') }} as f
    using (pays_code, date_id, sous_secteur_code, prelevement_code)
