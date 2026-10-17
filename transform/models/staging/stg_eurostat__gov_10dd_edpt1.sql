-- Dernier instantané de gov_10dd_edpt1 : dette notifiée (au sens de Maastricht), par instrument
-- pour l'ensemble des administrations et en total pour chaque sous-secteur.
select * from (
    {{ lire_eurostat('gov_10dd_edpt1', ['unit', 'sector', 'na_item']) }}
)
where annee >= 1995 and unit in ('MIO_EUR', 'MIO_NAC')
