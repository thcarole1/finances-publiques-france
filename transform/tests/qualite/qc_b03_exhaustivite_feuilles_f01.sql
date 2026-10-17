-- QC-B03 — Σ des feuilles (tous sous-secteurs + éliminations) = total publié (TE, TR), en S13.
with feuilles as (
    select p.code_eurostat as geo, f.date_id // 10000 as annee, t.sens, sum(f.valeur_meur) as somme
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    join {{ ref('dim_pays') }} as p using (pays_code)
    group by all
),
publie as (
    select geo, annee, case na_item when 'TE' then 'Dépense' else 'Recette' end as sens, valeur
    from {{ ref('stg_eurostat__gov_10a_main') }}
    where unit = 'MIO_EUR' and sector = 'S13' and na_item in ('TE', 'TR') and valeur is not null
)
select p.*, f.somme
from publie as p
left join feuilles as f using (geo, annee, sens)
where f.somme is null or {{ hors_tolerance('f.somme', 'p.valeur', 'QC_B03_exhaustivite_feuilles') }}
