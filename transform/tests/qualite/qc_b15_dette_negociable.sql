-- QC-B15 (avertissement) — Dette négociable de l'État : chaque axe (durée ; type de taux) redonne
-- l'encours total. Avertissement : la source présente un écart ponctuel (octobre 2017, type de taux).
{{ config(severity = 'warn') }}
with c as (
    select f.date_id, d.axe, sum(f.valeur_meur) as somme
    from {{ ref('fait_dette_negociable_etat') }} as f
    join {{ ref('dim_composante_dette_etat') }} as d using (composante_code)
    group by all
),
t as (
    select {{ fin_de_periode('b.periode') }} as date_id, b.valeur_m as total
    from {{ ref('stg_insee__bdm') }} as b
    join {{ ref('ref_series_insee') }} as r on r.idbank = b.idbank
    where r.usage = 'dette_negociable_total' and b.valeur_m is not null
)
select * from c join t using (date_id)
where {{ hors_tolerance('somme', 'total', 'QC_B15_dette_negociable') }}
