-- QC-B05 — Pour chaque feuille, Σ sous-secteurs + S13_ELIM (ou _NA) = valeur S13 calculée.
with s13 as (
    select geo, annee, transaction_code, valeur_meur
    from {{ ref('int_comptes_apu__feuilles') }}
    where sector = 'S13'
),
fait as (
    select p.code_eurostat as geo, f.date_id // 10000 as annee, f.transaction_code,
        sum(f.valeur_meur) as somme
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_pays') }} as p using (pays_code)
    group by all
)
select s.*, f.somme
from s13 as s
full join fait as f using (geo, annee, transaction_code)
where {{ hors_tolerance('coalesce(f.somme, 0)', 'coalesce(s.valeur_meur, 0)', 'QC_B05_consolidation') }}
