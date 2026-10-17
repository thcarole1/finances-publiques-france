-- F05 — Fait_Revisions : agrégats clés de la France et des autres pays, pour chaque millésime.
select
    p.pays_code,
    r.annee * 10000 + 1231                         as date_id,
    case r.na_item
        when 'TE' then 'DEPENSES_PUBLIQUES'
        when 'TR' then 'RECETTES_PUBLIQUES'
        when 'B9' then 'SOLDE_PUBLIC'
        when 'PIB' then 'PIB'
    end                                            as indicateur_code,
    m.millesime_id,
    round(r.valeur, 3)                             as valeur_meur
from {{ ref('stg_eurostat__revisions') }} as r
join {{ ref('ref_pays') }} as p on p.code_eurostat = r.geo
join {{ ref('dim_millesime') }} as m
    on m.source = 'eurostat' and m.jeu = r.jeu and m.date_collecte = r.date_collecte
where r.valeur is not null
