select * from (
    {{ lire_eurostat('nama_10_pe', ['unit', 'na_item']) }}
)
where annee >= 1995
