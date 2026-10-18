-- Dim_Edition_Prevision : chaque édition de prévisions (Commission, FMI), plus une ligne
-- « Réalité » qui porte les valeurs observées dans le graphique en spaghetti.
-- Date de publication conventionnelle : printemps 15/05, automne 15/11, hiver 15/02 ;
-- FMI avril 15/04, octobre 15/10 (seule l'année compte pour l'horizon de prévision).
with editions as (
    select distinct institution, edition_id, edition, annee_publication
    from {{ ref('int_previsions') }}
),
detail as (
    select *,
        split_part(edition, '-', 2) as saison,
        case split_part(edition, '-', 2)
            when 'hiver' then 2 when 'avril' then 4 when 'printemps' then 5
            when 'octobre' then 10 else 11 end as mois
    from editions
)
select
    edition_id,
    case institution when 'COMMISSION' then 'Commission européenne' else 'FMI' end as institution,
    case institution when 'COMMISSION' then 'Commission' else 'FMI' end
        || ' – ' || saison || ' ' || annee_publication                              as libelle,
    saison,
    annee_publication,
    make_date(annee_publication, mois, 15)                                         as date_publication,
    true                                                                           as est_prevision,
    cast(annee_publication * 100 + mois as integer)                                as ordre_tri
from detail
union all
select 'REALITE', 'Réalité', 'Réalité (dernières données)', null, null, null, false, 999999
