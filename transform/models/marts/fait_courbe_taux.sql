-- F12b — Fait_Courbe_Taux : courbe des taux de la zone euro (BCE), dernier jour ouvré de chaque
-- mois, par maturité et notation. Non additive.
with dernier_jour as (
    select *, row_number() over (
        partition by instrument, maturite_ans, date_trunc('month', jour) order by jour desc
    ) as rang
    from {{ ref('stg_bce__courbe_taux') }}
    where taux_pct is not null
),
millesime as (
    select millesime_id from {{ ref('dim_millesime') }}
    where source = 'bce' and jeu = 'courbe-taux' and est_dernier
)
select
    'EA'                                                         as pays_code,
    cast(strftime(last_day(jour), '%Y%m%d') as integer)          as date_id,
    maturite_ans,
    case instrument when 'G_N_A' then 'États notés AAA'
        else 'Ensemble des États de la zone euro' end            as notation,
    round(taux_pct, 4)                                           as taux_pct,
    'DEFINITIF'                                                  as statut_valeur,
    'BCE_COURBE-TAUX'                                            as source_id,
    (select millesime_id from millesime)                         as millesime_id
from dernier_jour
where rang = 1
