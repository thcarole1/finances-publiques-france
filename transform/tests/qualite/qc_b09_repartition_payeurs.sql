-- QC-B09 — La répartition par base économique conserve les montants :
-- pour chaque ligne de Fait_Prelevements, Σ des bases = montant d'origine.
{% set t = var('tolerances')['QC_B05_consolidation'] %}
with reparti as (
    select pays_code, date_id, sous_secteur_code, prelevement_code, sum(valeur_meur) as somme
    from {{ ref('fait_prelevements_fonction') }}
    group by all
)
select f.pays_code, f.date_id, f.sous_secteur_code, f.prelevement_code, f.valeur_meur, r.somme
from {{ ref('fait_prelevements') }} as f
left join reparti as r using (pays_code, date_id, sous_secteur_code, prelevement_code)
where r.somme is null
    or abs(r.somme - f.valeur_meur) > greatest({{ t.relative }} * abs(f.valeur_meur), 0.01)
