-- QC-B13 — La dette totale est la même dans les trois tables : par sous-secteur (consolidée),
-- par instrument et par détenteur (quand le détail par détenteur existe).
with s as (
    select pays_code, date_id, sum(valeur_meur) as par_sous_secteur
    from {{ ref('fait_dette') }} group by all
),
i as (
    select pays_code, date_id, sum(valeur_meur) as par_instrument
    from {{ ref('fait_dette_instrument') }} group by all
),
d as (
    select pays_code, date_id, sum(valeur_meur) as par_detenteur
    from {{ ref('fait_detention_dette') }} group by all
)
select *
from s
full join i using (pays_code, date_id)
left join d using (pays_code, date_id)
where {{ hors_tolerance('coalesce(par_instrument, 0)', 'coalesce(par_sous_secteur, 0)', 'QC_B13_coherence_dette') }}
    or (par_detenteur is not null
        and {{ hors_tolerance('par_detenteur', 'coalesce(par_sous_secteur, 0)', 'QC_B13_coherence_dette') }})
