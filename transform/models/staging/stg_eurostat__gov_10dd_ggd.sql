-- Dernier instantané de gov_10dd_ggd : dette des administrations publiques par détenteur.
select * from (
    {{ lire_eurostat('gov_10dd_ggd', ['na_item', 'sector2', 'sector', 'maturity', 'unit']) }}
)
where annee >= 1995 and unit in ('MIO_EUR', 'MIO_NAC') and na_item = 'GD'
    and sector = 'S13' and maturity = 'TOTAL'
