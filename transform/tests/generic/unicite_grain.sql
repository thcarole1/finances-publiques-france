{# QC-B02 — Aucune ligne en double sur les colonnes du grain. #}
{% test unicite_grain(model, colonnes) %}
select {{ colonnes | join(', ') }}, count(*) as nb
from {{ model }}
group by {{ colonnes | join(', ') }}
having count(*) > 1
{% endtest %}
