-- QC-B06 (avertissement) — La dette au 4e trimestre égale la dette annuelle notifiée.
-- Avertissement seulement : les deux jeux Eurostat ne sont pas mis à jour le même jour.
{{ config(severity = 'warn') }}
with t as (
    select pays_code, date_id, sum(valeur_meur) as trimestrielle
    from {{ ref('fait_dette_trimestrielle') }}
    where date_id % 10000 = 1231
    group by all
),
a as (
    select pays_code, date_id, sum(valeur_meur) as annuelle
    from {{ ref('fait_dette') }} group by all
)
select * from t join a using (pays_code, date_id)
where {{ hors_tolerance('trimestrielle', 'annuelle', 'QC_B06_dette_t4_annuelle') }}
