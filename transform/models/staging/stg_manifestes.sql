-- Manifestes de tous les instantanés bruts : base de Dim_Millesime.
select
    source,
    jeu,
    cast(date_collecte as date)                  as date_collecte,
    cast(nullif(date_publication, '') as date)   as date_publication,
    cast(horodatage_utc as timestamp)            as horodatage_utc,
    len(fichiers)                                as nb_fichiers
from read_json(
    'data/raw/*/*/*/manifest.json',
    columns = {
        source: 'varchar', jeu: 'varchar', date_collecte: 'varchar',
        date_publication: 'varchar', horodatage_utc: 'varchar', fichiers: 'json[]'
    }
)
