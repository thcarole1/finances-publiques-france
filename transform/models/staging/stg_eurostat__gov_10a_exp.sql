-- Dernier instantané de gov_10a_exp (fonctions COFOG × nature).
select * from (
    {{ lire_eurostat('gov_10a_exp', ['unit', 'sector', 'cofog99 as cofog', 'na_item']) }}
)
where annee >= 1995 and unit in ('MIO_EUR', 'MIO_NAC')
