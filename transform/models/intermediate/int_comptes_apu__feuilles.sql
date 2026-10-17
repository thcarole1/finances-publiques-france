-- Feuilles de recettes et de dépenses (docs/04, Dim_Transaction) par pays, année, secteur.
-- Une feuille = Σ coefficient × poste Eurostat ; la feuille « Autres » est le résidu qui garantit
-- Σ feuilles = total publié (TE pour les dépenses, TR pour les recettes).
with obs as (
    select geo, annee, sector, unit, na_item, valeur, flag
    from {{ ref('stg_eurostat__gov_10a_main') }}
),
formule as (
    select f.transaction_code, f.na_item, f.coefficient, t.sens
    from {{ ref('ref_formule_comptes_apu') }} as f
    join {{ ref('ref_transaction') }} as t using (transaction_code)
),
ancres as (
    -- Combinaisons pour lesquelles le total publié existe.
    select distinct geo, annee, sector, unit,
        case na_item when 'TE' then 'Dépense' else 'Recette' end as sens
    from obs
    where na_item in ('TE', 'TR') and valeur is not null
),
calcul as (
    select
        a.geo, a.annee, a.sector, a.unit, f.transaction_code,
        sum(f.coefficient * coalesce(o.valeur, 0))       as valeur,
        count(o.valeur)                                  as nb_composantes,
        string_agg(coalesce(o.flag, ''), '')             as flags
    from ancres as a
    join formule as f on f.sens = a.sens
    left join obs as o
        on o.geo = a.geo and o.annee = a.annee and o.sector = a.sector
        and o.unit = a.unit and o.na_item = f.na_item
    group by all
)
select
    geo, annee, sector, transaction_code,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(flags, '')                            as flags
from calcul
where nb_composantes > 0
group by all
