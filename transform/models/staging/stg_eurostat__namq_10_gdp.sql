-- Dernier instantané de namq_10_gdp : PIB trimestriel à prix courants, brut et CVS-CJO.
select * from (
    {{ lire_eurostat('namq_10_gdp', ['unit', 's_adj', 'na_item']) }}
)
where annee >= 1995 and na_item = 'B1GQ'
