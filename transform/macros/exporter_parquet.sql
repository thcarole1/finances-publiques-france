{#
  Exporte une table du modèle vers data/curated/<table>.parquet (compression ZSTD).
  Les lignes sont triées pour que deux constructions à partir des mêmes données produisent
  des fichiers identiques (pas de différence Git ni de pull request de données inutile).
#}
{% macro exporter_parquet(relation) %}
  copy (select * from {{ relation }} order by all)
    to '{{ var("dossier_curated") }}/{{ relation.identifier }}.parquet'
    (format parquet, compression zstd)
{% endmacro %}
