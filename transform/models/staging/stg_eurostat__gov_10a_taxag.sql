-- Dernier instantané de gov_10a_taxag, filtré sur la période et les unités utiles.
select * from (
    {{ lire_eurostat('gov_10a_taxag', ['unit', 'sector', 'na_item']) }}
)
where annee >= 1995 and unit in ('MIO_EUR', 'MIO_NAC')
