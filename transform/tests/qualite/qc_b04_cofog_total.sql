-- QC-B04 — Σ des fonctions COFOG (feuilles, tous sous-secteurs + éliminations) = dépenses totales
-- publiées dans le même jeu (gov_10a_exp, TOTAL × TE, S13).
with feuilles as (
    select p.code_eurostat as geo, f.date_id // 10000 as annee, sum(f.valeur_meur) as somme
    from {{ ref('fait_depenses_fonction') }} as f
    join {{ ref('dim_pays') }} as p using (pays_code)
    group by all
),
publie as (
    select geo, annee, valeur
    from {{ ref('stg_eurostat__gov_10a_exp') }}
    where unit = 'MIO_EUR' and sector = 'S13' and cofog = 'TOTAL' and na_item = 'TE'
        and valeur is not null
)
select p.*, f.somme
from publie as p
left join feuilles as f using (geo, annee)
where f.somme is null or {{ hors_tolerance('f.somme', 'p.valeur', 'QC_B04_cofog_total') }}
