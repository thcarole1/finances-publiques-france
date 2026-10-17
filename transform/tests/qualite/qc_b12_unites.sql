-- QC-B12 — Ordre de grandeur : dépenses publiques entre 20 % et 75 % du PIB
-- (détecte une erreur d'échelle millions / milliards ou une erreur de jointure).
{% set t = var('tolerances')['QC_B12_unites'] %}
with dep as (
    select f.pays_code, f.date_id, sum(f.valeur_meur) as depenses
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    where t.sens = 'Dépense'
    group by all
)
select d.pays_code, d.date_id, 100 * d.depenses / m.pib_meur as depenses_pct_pib
from dep as d
join {{ ref('fait_macro_annuel') }} as m using (pays_code, date_id)
where m.pib_meur > 0
    and 100 * d.depenses / m.pib_meur not between {{ t.depenses_pct_pib_min }} and {{ t.depenses_pct_pib_max }}
