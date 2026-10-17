{#
  Exporte une table du modèle vers data/curated/<table>.parquet (compression ZSTD).
  Les grandes tables partitionnées (lot 7) utiliseront un dossier par table.
#}
{% macro exporter_parquet(relation) %}
  copy {{ relation }} to '{{ var("dossier_curated") }}/{{ relation.identifier }}.parquet'
    (format parquet, compression zstd)
{% endmacro %}
