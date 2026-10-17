-- Dim_Date : une ligne par jour, de date_debut à date_fin (variables du projet).
-- Convention : un fait annuel est daté du 31/12, trimestriel du dernier jour du trimestre,
-- mensuel du dernier jour du mois (docs/04-modele-dimensions.md).

with jours as (
    select cast(range as date) as date
    from range(
        date '{{ var("date_debut") }}',
        date '{{ var("date_fin") }}' + interval 1 day,
        interval 1 day
    )
),

periodes as (
    select * from {{ ref('ref_periodes_historiques') }}
),

-- Années pour lesquelles au moins un pays a des comptes annuels publiés (filtre des segments
-- « Année » du rapport : on n'y propose pas 1990 ni 2075).
annees_disponibles as (
    select distinct date_id // 10000 as annee
    from {{ ref('fait_comptes_apu_annuels') }}
)

select
    cast(strftime(j.date, '%Y%m%d') as integer)                       as date_id,
    j.date                                                             as date,
    cast(year(j.date) as integer)                                      as annee,
    cast(quarter(j.date) as integer)                                   as trimestre,
    cast(month(j.date) as integer)                                     as mois,
    cast(year(j.date) as varchar) || '-T' || cast(quarter(j.date) as varchar)
                                                                       as annee_trimestre,
    cast(year(j.date) as varchar) || '-' || lpad(cast(month(j.date) as varchar), 2, '0')
                                                                       as annee_mois,
    ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
     'septembre', 'octobre', 'novembre', 'décembre'][month(j.date)]    as mois_libelle,
    cast(year(j.date) // 10 * 10 as varchar) || 's'                    as decennie,
    j.date = last_day(j.date)                                          as est_fin_mois,
    j.date = last_day(j.date) and month(j.date) in (3, 6, 9, 12)       as est_fin_trimestre,
    j.date = last_day(j.date) and month(j.date) = 12                   as est_fin_annee,
    p.periode_code                                                     as periode_historique_code,
    p.libelle                                                          as periode_historique,
    a.annee is not null                                                as est_annee_disponible
from jours as j
left join periodes as p
    on j.date between p.date_debut and p.date_fin
left join annees_disponibles as a
    on year(j.date) = a.annee
order by j.date
