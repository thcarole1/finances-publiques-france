-- Tous les millésimes des agrégats clés (table des révisions, docs/05 F05).
with apu as (
    select date_collecte, date_maj_producteur, geo, annee, na_item, valeur, flag
    from ({{ lire_eurostat('gov_10a_main', ['unit', 'sector', 'na_item'], tous_millesimes=true) }})
    where unit = 'MIO_EUR' and sector = 'S13' and na_item in ('TE', 'TR', 'B9') and annee >= 1995
),
pib as (
    select date_collecte, date_maj_producteur, geo, annee, 'PIB' as na_item, valeur, flag
    from ({{ lire_eurostat('nama_10_gdp', ['unit', 'na_item'], tous_millesimes=true) }})
    where unit = 'CP_MEUR' and na_item = 'B1GQ' and annee >= 1995
)
select 'gov_10a_main' as jeu, * from apu
union all
select 'nama_10_gdp' as jeu, * from pib
