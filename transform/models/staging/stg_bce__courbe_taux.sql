-- Courbe des taux de la zone euro (BCE, flux YC), dernier instantané : une ligne par jour ouvré,
-- maturité et notation. G_N_A = emprunts d'État notés AAA ; G_N_C = tous les emprunts d'État.
with brut as (
    select *, regexp_extract(filename, '/(\d{4}-\d{2}-\d{2})/', 1) as date_collecte
    from read_csv('data/raw/bce/courbe-taux/*/*.csv.gz', header = true, all_varchar = true,
        filename = true)
)
select
    cast(date_collecte as date)                                       as date_collecte,
    cast("TIME_PERIOD" as date)                                       as jour,
    cast(regexp_extract("DATA_TYPE_FM", 'SR_(\d+)Y', 1) as integer)   as maturite_ans,
    "INSTRUMENT_FM"                                                   as instrument,
    try_cast("OBS_VALUE" as double)                                   as taux_pct
from brut
where date_collecte = (select max(date_collecte) from brut)
