-- QC-A03 (avertissement) — Révision du solde public de plus de 0,3 point de PIB entre les deux
-- derniers millésimes.
{{ config(severity = 'warn') }}
{% set seuil = var('tolerances')['QC_A03_revision']['points_pib'] %}
with r as (
    select f.pays_code, f.date_id, m.rang_recence, f.valeur_meur
    from {{ ref('fait_revisions') }} as f
    join {{ ref('dim_millesime') }} as m using (millesime_id)
    where f.indicateur_code = 'SOLDE_PUBLIC' and m.rang_recence <= 2
),
pib as (select pays_code, date_id, pib_meur from {{ ref('fait_macro_annuel') }})
select r1.pays_code, r1.date_id,
    100 * (r1.valeur_meur - r2.valeur_meur) / pib.pib_meur as revision_points_pib
from r as r1
join r as r2 on r2.pays_code = r1.pays_code and r2.date_id = r1.date_id and r2.rang_recence = 2
join pib on pib.pays_code = r1.pays_code and pib.date_id = r1.date_id
where r1.rang_recence = 1
    and abs(100 * (r1.valeur_meur - r2.valeur_meur) / pib.pib_meur) > {{ seuil }}
