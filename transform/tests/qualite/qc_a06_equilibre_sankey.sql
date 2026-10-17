-- QC-A06b (avertissement) — Équilibre des nœuds du Sankey : pour chaque administration,
-- ce qui entre et ce qui sort diffèrent de moins de 2 % (écarts dus aux dates de mise à jour
-- différentes des jeux Eurostat).
{{ config(severity = 'warn') }}
with n as (
    select pays_code, date_id, cible as noeud, sum(valeur_meur) as entree, 0 as sortie
    from {{ ref('pres_flux_sankey') }} where lecture = 'Par base économique' group by all
    union all
    select pays_code, date_id, source, 0, sum(valeur_meur)
    from {{ ref('pres_flux_sankey') }} where lecture = 'Par base économique' group by all
),
b as (
    select pays_code, date_id, noeud, sum(entree) as entree, sum(sortie) as sortie
    from n group by all
    having sum(entree) > 1000 and sum(sortie) > 1000
)
select *, abs(entree - sortie) / greatest(entree, sortie) as ecart
from b
where abs(entree - sortie) / greatest(entree, sortie) > 0.02
