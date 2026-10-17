-- QC-A04 (avertissement) — Cohérence entre jeux : dépenses totales COFOG (gov_10a_exp) vs
-- comptes principaux (gov_10a_main). Écart attendu faible, dû aux dates de mise à jour.
{{ config(severity = 'warn') }}
{% set seuil = var('tolerances')['QC_A04_coherence_sources']['relative'] %}
with cofog as (
    select pays_code, date_id, sum(valeur_meur) as v from {{ ref('fait_depenses_fonction') }}
    group by all
),
comptes as (
    select f.pays_code, f.date_id, sum(f.valeur_meur) as v
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    where t.sens = 'Dépense' group by all
)
select c.pays_code, c.date_id, c.v as cofog, k.v as comptes, c.v / k.v - 1 as ecart
from cofog as c join comptes as k using (pays_code, date_id)
where abs(c.v / k.v - 1) > {{ seuil }}
