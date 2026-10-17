{#
  Lit un jeu Eurostat SDMX-CSV depuis les instantanés bruts data/raw/eurostat/<jeu>/<date>/.
  - tous_millesimes=false : uniquement l'instantané le plus récent (cas général) ;
  - tous_millesimes=true  : tous les instantanés, avec leur date de collecte (table des révisions).
  Renvoie des colonnes normalisées : date_collecte, unit, sector, cofog, na_item, geo, annee,
  valeur (double), flag, date_maj_producteur, et periode (TIME_PERIOD brut : « 2024 »,
  « 2024-Q4 » ou « 2024-12 ») pour les jeux infra-annuels.
#}
{% macro lire_eurostat(jeu, colonnes_dimensions, tous_millesimes=false) %}
  with brut as (
      select
          *,
          regexp_extract(filename, '/(\d{4}-\d{2}-\d{2})/', 1) as date_collecte
      from read_csv(
          'data/raw/eurostat/{{ jeu }}/*/*.csv.gz',
          header = true, all_varchar = true, union_by_name = true, filename = true
      )
  ),
  selection as (
      select * from brut
      {% if not tous_millesimes %}
      where date_collecte = (select max(date_collecte) from brut)
      {% endif %}
  )
  select
      cast(date_collecte as date)                     as date_collecte,
      {% for c in colonnes_dimensions %}{{ c }},
      {% endfor %}
      geo,
      "TIME_PERIOD"                                   as periode,
      cast(left("TIME_PERIOD", 4) as integer)         as annee,
      try_cast("OBS_VALUE" as double)                 as valeur,
      nullif("OBS_FLAG", '')                          as flag,
      cast(strptime("LAST UPDATE", '%d/%m/%y %H:%M:%S') as date) as date_maj_producteur
  from selection
{% endmacro %}
