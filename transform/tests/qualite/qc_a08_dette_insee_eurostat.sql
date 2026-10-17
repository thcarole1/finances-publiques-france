-- QC-A08 (avertissement) — Dette trimestrielle de la France : INSEE et Eurostat concordent à 1 %.
{{ config(severity = 'warn') }}
with i as (
    select date_id, sum(valeur_meur) as insee from {{ ref('fait_dette_contributions') }} group by all
),
e as (
    select date_id, sum(valeur_meur) as eurostat
    from {{ ref('fait_dette_trimestrielle') }} where pays_code = 'FR' group by all
)
select * from i join e using (date_id)
where {{ hors_tolerance('insee', 'eurostat', 'QC_A04_coherence_sources') }}
