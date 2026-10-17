-- Dim_Millesime : une ligne par instantané collecté (source × jeu × date de collecte).
select
    upper(source || '_' || jeu) || '_' || strftime(date_collecte, '%Y-%m-%d') as millesime_id,
    upper(source || '_' || jeu)                                                as source_id,
    source,
    jeu,
    coalesce(date_publication, date_collecte)                                  as date_publication,
    date_collecte,
    'Données ' || source || ' ' || jeu || ' mises à jour le '
        || strftime(coalesce(date_publication, date_collecte), '%d/%m/%Y')     as libelle,
    cast(row_number() over (partition by source, jeu order by date_collecte desc) as integer)
                                                                               as rang_recence,
    row_number() over (partition by source, jeu order by date_collecte desc) = 1 as est_dernier
from {{ ref('stg_manifestes') }}
