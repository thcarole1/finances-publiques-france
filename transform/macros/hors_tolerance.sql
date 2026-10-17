{# Vrai si l'écart entre deux montants dépasse la tolérance (relative ou absolue, la plus large). #}
{% macro hors_tolerance(a, b, code) %}
  {% set t = var('tolerances')[code] %}
  abs(({{ a }}) - ({{ b }})) > greatest(
      {{ t.get('relative', 0) }} * abs({{ b }}),
      {{ t.get('absolue_meur', 0) }}
  )
{% endmacro %}
