-- QC-B14 — Les contributions des administrations (INSEE) redonnent la dette totale publiée.
with c as (
    select date_id, sum(valeur_meur) as somme from {{ ref('fait_dette_contributions') }} group by all
),
t as (
    select {{ fin_de_periode('b.periode') }} as date_id, b.valeur_m as total
    from {{ ref('stg_insee__bdm') }} as b
    join {{ ref('ref_series_insee') }} as r on r.idbank = b.idbank
    where r.usage = 'dette_total' and b.valeur_m is not null
)
select * from c full join t using (date_id)
where {{ hors_tolerance('coalesce(somme, 0)', 'coalesce(total, 0)', 'QC_B14_contributions_dette') }}
