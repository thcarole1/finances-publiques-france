-- Valeurs réalisées (dernières données publiées) des variables suivies dans les prévisions.
with comptes as (
    select f.pays_code, f.date_id // 10000 as annee,
        sum(case when t.sens = 'Recette' then f.valeur_meur else -f.valeur_meur end) as solde,
        sum(case when f.transaction_code = 'D41_PAY' then f.valeur_meur else 0 end) as interets
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    group by all
),
dette as (
    select pays_code, date_id // 10000 as annee, sum(valeur_meur) as dette
    from {{ ref('fait_dette') }} group by all
),
macro as (
    select pays_code, date_id // 10000 as annee, pib_meur, croissance_volume_pct
    from {{ ref('fait_macro_annuel') }}
)
select pays_code, annee, 'DETTE' as variable_code, 100 * d.dette / m.pib_meur as valeur
from dette as d join macro as m using (pays_code, annee)
union all
select pays_code, annee, 'SOLDE', 100 * c.solde / m.pib_meur
from comptes as c join macro as m using (pays_code, annee)
union all
select pays_code, annee, 'SOLDE_PRIMAIRE', 100 * (c.solde + c.interets) / m.pib_meur
from comptes as c join macro as m using (pays_code, annee)
union all
select pays_code, annee, 'CROISSANCE', croissance_volume_pct
from macro where croissance_volume_pct is not null
