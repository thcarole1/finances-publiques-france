-- Feuilles COFOG × nature : sous-fonctions de niveau 2, plus résidus « non ventilé »
-- par fonction de niveau 1 (GFxx_NV) et sur le total (GF_NV).
with natures as (
    select o.geo, o.annee, o.sector, o.unit, o.cofog, f.transaction_code, o.valeur, o.flag
    from {{ ref('stg_eurostat__gov_10a_exp') }} as o
    join {{ ref('ref_formule_depense_fonction') }} as f on f.na_item = o.na_item
),
total_natures as (
    -- Nature non ventilée = TE − Σ natures publiées (années anciennes de certains pays,
    -- où seule la dépense totale par fonction est disponible).
    select te.geo, te.annee, te.sector, te.unit, te.cofog, 'NV_PAY' as transaction_code,
        te.valeur - coalesce(sum(n.valeur), 0) as valeur, te.flag
    from {{ ref('stg_eurostat__gov_10a_exp') }} as te
    left join natures as n
        on n.geo = te.geo and n.annee = te.annee and n.sector = te.sector
        and n.unit = te.unit and n.cofog = te.cofog
    where te.na_item = 'TE' and te.valeur is not null
    group by te.geo, te.annee, te.sector, te.unit, te.cofog, te.valeur, te.flag
),
obs as (
    select * from natures
    union all
    select * from total_natures where abs(valeur) > 0.05
),
n2 as (
    select geo, annee, sector, unit, transaction_code, cofog, valeur, flag
    from obs where length(cofog) = 6 and valeur is not null
),
n1 as (select * from obs where length(cofog) = 4 and cofog like 'GF%'),
total as (select * from obs where cofog = 'TOTAL' and valeur is not null),
somme_n2 as (
    select geo, annee, sector, unit, transaction_code, substr(cofog, 1, 4) as cofog_n1,
        sum(valeur) as valeur
    from n2 group by all
),
residu_n1 as (
    select n1.geo, n1.annee, n1.sector, n1.unit, n1.transaction_code,
        n1.cofog || '_NV' as cofog,
        n1.valeur - coalesce(s.valeur, 0) as valeur, n1.flag
    from n1
    left join somme_n2 as s
        on s.geo = n1.geo and s.annee = n1.annee and s.sector = n1.sector
        and s.unit = n1.unit and s.transaction_code = n1.transaction_code and s.cofog_n1 = n1.cofog
    where n1.valeur is not null
),
somme_n1 as (
    -- Ce que couvrent les fonctions de niveau 1 (publiées, ou à défaut leurs sous-fonctions).
    select geo, annee, sector, unit, transaction_code, sum(valeur) as valeur from (
        select geo, annee, sector, unit, transaction_code, valeur from n1 where valeur is not null
        union all
        select s.geo, s.annee, s.sector, s.unit, s.transaction_code, s.valeur
        from somme_n2 as s
        anti join (select * from n1 where valeur is not null) as n1p
            on n1p.geo = s.geo and n1p.annee = s.annee and n1p.sector = s.sector
            and n1p.unit = s.unit and n1p.transaction_code = s.transaction_code
            and n1p.cofog = s.cofog_n1
    ) group by all
),
residu_total as (
    select t.geo, t.annee, t.sector, t.unit, t.transaction_code, 'GF_NV' as cofog,
        t.valeur - coalesce(s.valeur, 0) as valeur, t.flag
    from total as t
    left join somme_n1 as s
        on s.geo = t.geo and s.annee = t.annee and s.sector = t.sector
        and s.unit = t.unit and s.transaction_code = t.transaction_code
),
feuilles as (
    select * from n2
    union all select * from residu_n1
    union all select * from residu_total
)
select
    geo, annee, sector, cofog, transaction_code,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(coalesce(flag, ''), '')               as flags
from feuilles
group by all
