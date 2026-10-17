-- Dim_Date doit couvrir chaque jour de la plage, sans trou ni doublon.
-- Renvoie une ligne (= échec) si le nombre de jours ne correspond pas.
select count(*) as nb_jours
from {{ ref('dim_date') }}
having count(*) != date_diff('day', date '{{ var("date_debut") }}', date '{{ var("date_fin") }}') + 1
