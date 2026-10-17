-- QC-B10 — Recettes − dépenses (feuilles) = capacité / besoin de financement publié (B9), en S13.
with solde as (
    select p.code_eurostat as geo, f.date_id // 10000 as annee,
        sum(case t.sens when 'Recette' then f.valeur_meur else -f.valeur_meur end) as solde
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    join {{ ref('dim_pays') }} as p using (pays_code)
    group by all
),
b9 as (
    select geo, annee, valeur
    from {{ ref('stg_eurostat__gov_10a_main') }}
    where unit = 'MIO_EUR' and sector = 'S13' and na_item = 'B9' and valeur is not null
)
select b.*, s.solde
from b9 as b
join solde as s using (geo, annee)
where {{ hors_tolerance('s.solde', 'b.valeur', 'QC_B10_identite_solde') }}
