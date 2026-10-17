-- Le mécanisme de consolidation suppose une et une seule ligne d'élimination.
select count(*) as nb
from {{ ref('dim_sous_secteur') }}
where est_elimination
having count(*) != 1
