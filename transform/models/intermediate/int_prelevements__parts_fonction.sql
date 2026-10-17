-- Part de chaque base économique (DG TAXUD) dans chaque feuille de prélèvement,
-- par pays et par année. Σ des parts = 1 pour chaque pays × année × prélèvement couvert.
with ntl as (
    select geo, annee, sto, fonction, valeur
    from {{ ref('stg_taxud__ntl') }}
    where fonction in ('C', 'LEYRS', 'LEES', 'LNON', 'KIC', 'KIH', 'KISE', 'KS', 'SPLIT1', 'SPLIT2')
        and valeur is not null
),
feuilles as (
    select prelevement_code from {{ ref('ref_prelevement') }} where not est_non_ventile
),
correspondance as (
    -- Code SEC national (ex. D2121, D611C, D613CE) → feuille du modèle : plus long préfixe.
    select s.sto, (
        select f.prelevement_code from feuilles as f
        where starts_with(s.sto, f.prelevement_code)
        order by length(f.prelevement_code) desc
        limit 1
    ) as prelevement_code
    from (select distinct sto from ntl) as s
    union all
    -- Feuilles « non ventilé » (ex. D51_NV) : composition de tous les impôts du niveau parent
    -- (ex. tous les D51…), appliquée quand le producteur ne publie pas le détail.
    select s.sto, r.prelevement_code
    from (select distinct sto from ntl) as s
    join {{ ref('ref_prelevement') }} as r
        on r.est_non_ventile and r.prelevement_code <> 'TOTAL_NV'
        and starts_with(s.sto, replace(r.prelevement_code, '_NV', ''))
),
repartitions as (
    -- Répartitions SPLIT1 / SPLIT2 normalisées (Σ = 1), prolongées aux années non couvertes
    -- par la dernière année disponible (ou la première pour les années antérieures).
    select repartition, geo, annee, fonction,
        part / sum(part) over (partition by repartition, geo, annee) as part
    from {{ ref('stg_taxud__repartition_ir') }}
),
repartitions_annees as (
    select g.repartition, g.geo, a.annee,
        coalesce(
            (select max(r.annee) from repartitions as r
             where r.repartition = g.repartition and r.geo = g.geo and r.annee <= a.annee),
            (select min(r.annee) from repartitions as r
             where r.repartition = g.repartition and r.geo = g.geo)
        ) as annee_source
    from (select distinct repartition, geo from repartitions) as g
    cross join (select range::integer as annee from range(1995, 2041)) as a
),
repartitions_completes as (
    select ra.repartition, ra.geo, ra.annee, r.fonction, r.part
    from repartitions_annees as ra
    join repartitions as r
        on r.repartition = ra.repartition and r.geo = ra.geo and r.annee = ra.annee_source
),
montants as (
    select n.geo, n.annee, c.prelevement_code, n.fonction, n.valeur
    from ntl as n join correspondance as c on c.sto = n.sto
    where n.fonction not like 'SPLIT%' and c.prelevement_code is not null
    union all
    select n.geo, n.annee, c.prelevement_code, coalesce(r.fonction, 'NV'),
        n.valeur * coalesce(r.part, 1)
    from ntl as n
    join correspondance as c on c.sto = n.sto
    left join repartitions_completes as r
        on r.repartition = n.fonction and r.geo = n.geo and r.annee = n.annee
    where n.fonction like 'SPLIT%' and c.prelevement_code is not null
),
agreges as (
    select geo, annee, prelevement_code, fonction, sum(valeur) as valeur
    from montants group by all
)
select
    geo, annee, prelevement_code, fonction as fonction_code,
    valeur / sum(valeur) over (partition by geo, annee, prelevement_code) as part
from agreges
-- Composition stable uniquement : le total doit représenter au moins la moitié de la somme des
-- montants en valeur absolue (sinon les parts exploseraient ; le prélèvement passe en repli).
qualify sum(valeur) over (partition by geo, annee, prelevement_code)
    >= 0.5 * sum(abs(valeur)) over (partition by geo, annee, prelevement_code)
    and sum(valeur) over (partition by geo, annee, prelevement_code) > 0
