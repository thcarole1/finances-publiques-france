-- QC-A01 (avertissement) — Pays sans comptes publiés pour une année couverte par les autres.
{{ config(severity = 'warn') }}
with annees as (
    select distinct date_id from {{ ref('fait_comptes_apu_annuels') }}
    where date_id < (select max(date_id) from {{ ref('fait_comptes_apu_annuels') }})
),
pays as (select pays_code from {{ ref('dim_pays') }} where source_reference = 'Eurostat')
select p.pays_code, a.date_id
from pays as p cross join annees as a
anti join (select distinct pays_code, date_id from {{ ref('fait_comptes_apu_annuels') }}) as f
    using (pays_code, date_id)
