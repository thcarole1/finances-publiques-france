-- Les listes nationales ne doivent pas porter une base économique à la fois sur une ligne
-- totale (_T) et sur ses lignes de détail pour un même code : sinon double compte.
with valides as (
    select geo, annee, sto, details
    from {{ ref('stg_taxud__ntl') }}
    where fonction in ('C', 'LEYRS', 'LEES', 'LNON', 'KIC', 'KIH', 'KISE', 'KS', 'SPLIT1', 'SPLIT2')
        and valeur is not null and valeur <> 0
)
select t.geo, t.annee, t.sto
from valides as t
join valides as d
    on d.geo = t.geo and d.annee = t.annee and d.sto = t.sto and d.details <> '_T'
where t.details = '_T'
group by all
