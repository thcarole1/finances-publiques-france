{# Date (AAAAMMJJ, entier) du dernier jour d'une période SDMX : « 2024 », « 2024-Q4 » ou « 2024-12 ». #}
{% macro fin_de_periode(periode) %}
  cast(strftime(
      case
          when {{ periode }} like '%-Q%' then last_day(make_date(
              cast(left({{ periode }}, 4) as integer),
              cast(right({{ periode }}, 1) as integer) * 3, 1))
          when length({{ periode }}) = 7 then last_day(strptime({{ periode }} || '-01', '%Y-%m-%d'))
          else make_date(cast(left({{ periode }}, 4) as integer), 12, 31)
      end, '%Y%m%d') as integer)
{% endmacro %}
