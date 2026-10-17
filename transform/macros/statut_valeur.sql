{# Statut d'une valeur calculée à partir des drapeaux Eurostat de ses composantes. #}
{% macro statut_valeur(colonne_flags) %}
  case
      when {{ colonne_flags }} like '%p%' then 'PROVISOIRE'
      when {{ colonne_flags }} like '%e%' or {{ colonne_flags }} like '%s%' then 'ESTIME'
      else 'DEFINITIF'
  end
{% endmacro %}
