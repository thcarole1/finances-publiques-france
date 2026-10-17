select * from (
    {{ lire_eurostat('nama_10_gdp', ['unit', 'na_item']) }}
)
where annee >= 1995
