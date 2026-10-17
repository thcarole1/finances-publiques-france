-- QC-A05 (avertissement) — Les transferts entre sous-secteurs (F06) expliquent les éliminations
-- de la consolidation (F01, S13_ELIM) sur les dépenses de revenus de la propriété, transferts
-- courants et transferts en capital. Écart attendu faible (flux non ventilés par contrepartie).
{{ config(severity = 'warn') }}
with transferts as (
    select pays_code, date_id, sum(valeur_meur) as v
    from {{ ref('fait_transferts_apu') }} group by all
),
eliminations as (
    select pays_code, date_id, -sum(valeur_meur) as v
    from {{ ref('fait_comptes_apu_annuels') }}
    where sous_secteur_code = 'S13_ELIM'
        and transaction_code in ('D41_PAY', 'D4X_PAY', 'D7_PAY', 'D9_PAY')
    group by all
)
select e.pays_code, e.date_id, e.v as eliminations, t.v as transferts
from eliminations as e
left join transferts as t using (pays_code, date_id)
where e.v > 1000 and abs(coalesce(t.v, 0) / e.v - 1) > 0.05
