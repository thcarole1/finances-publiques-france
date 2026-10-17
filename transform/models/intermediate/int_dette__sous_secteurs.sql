-- Dette (au sens de Maastricht) par pays, année et secteur : total GD, S13 et sous-secteurs.
-- La dette d'un sous-secteur inclut ce qu'il doit aux autres administrations ; la consolidation
-- (fait_dette) retire ces dettes croisées via la ligne S13_ELIM.
select
    geo, annee, sector,
    max(case when unit = 'MIO_EUR' then valeur end) as valeur_meur,
    max(case when unit = 'MIO_NAC' then valeur end) as valeur_mnac,
    string_agg(coalesce(flag, ''), '')               as flags
from {{ ref('stg_eurostat__gov_10dd_edpt1') }}
where na_item = 'GD' and valeur is not null
group by all
