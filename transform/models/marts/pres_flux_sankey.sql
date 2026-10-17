-- Pres_Flux_Sankey : flux pré-calculés pour le diagramme de Sankey « où va l'argent ? ».
-- Table de présentation (dérivée, jamais source de vérité). Trois étapes par pays × année :
--   1. payeur (ou base économique) → administration qui encaisse :
--      prélèvements (Fait_Prelevements_Fonction), autres recettes, emprunt (déficit) ;
--   2. administration qui encaisse → administration qui dépense :
--      ce qu'elle garde, et les transferts aux autres administrations (Fait_Transferts_APU) ;
--   3. administration qui dépense → fonction (COFOG niveau 1), dépense consolidée : les
--      éliminations par fonction (S13_ELIM) sont imputées aux administrations versantes par un
--      ajustement RAS (int_sankey__imputation_eliminations). Un excédent forme un flux « Excédent ».
-- Chaque ligne existe pour les trois lectures (légale, économique, par base) afin qu'un segment
-- « lecture » filtre l'étape 1 sans faire disparaître les étapes 2 et 3.
with ss as (
    select sous_secteur_code, libelle_court
    from {{ ref('dim_sous_secteur') }}
    where sous_secteur_code in ('S1311', 'S1312', 'S1313', 'S1314', '_NA')
),
lectures as (
    select unnest(['Qui verse (lecture légale)', 'Qui supporte (lecture économique)', 'Par base économique']) as lecture
),

-- Étape 1a : prélèvements par payeur, vers l'administration bénéficiaire
prelevements as (
    select f.pays_code, f.date_id, l.lecture,
        case l.lecture
            when 'Qui verse (lecture légale)' then d.payeur_legal
            when 'Qui supporte (lecture économique)' then d.payeur_economique
            else d.libelle
        end as source,
        'Encaisse : ' || s.libelle_court as cible,
        f.sous_secteur_code,
        sum(f.valeur_meur) as valeur
    from {{ ref('fait_prelevements_fonction') }} as f
    join {{ ref('dim_fonction_economique') }} as d using (fonction_code)
    join ss as s using (sous_secteur_code)
    cross join lectures as l
    group by all
),
-- Comptes par sous-secteur (non consolidés) : recettes, dépenses, recettes non fiscales
comptes as (
    select f.pays_code, f.date_id, f.sous_secteur_code,
        sum(f.valeur_meur) filter (where t.sens = 'Dépense') as depenses,
        sum(f.valeur_meur) filter (where t.sens = 'Recette') as recettes,
        sum(f.valeur_meur) filter (
            where t.sens = 'Recette'
            and f.transaction_code in ('P1_REC', 'D4_REC', 'D7_REC', 'D9X_REC', 'AUTRES_REC')
        ) as recettes_non_fiscales
    from {{ ref('fait_comptes_apu_annuels') }} as f
    join {{ ref('dim_transaction') }} as t using (transaction_code)
    where f.sous_secteur_code in (select sous_secteur_code from ss)
    group by all
),
recus as (
    select pays_code, date_id, sous_secteur_receveur_code as sous_secteur_code,
        sum(valeur_meur) as valeur
    from {{ ref('fait_transferts_apu') }} group by all
),
verses as (
    select pays_code, date_id, sous_secteur_versant_code as sous_secteur_code,
        sum(valeur_meur) as valeur
    from {{ ref('fait_transferts_apu') }} group by all
),
-- Étape 1b : autres recettes (hors transferts reçus d'autres administrations) et emprunt
autres_et_emprunt as (
    select c.pays_code, c.date_id, c.sous_secteur_code,
        c.recettes_non_fiscales - coalesce(r.valeur, 0) as autres_recettes,
        greatest(c.depenses - c.recettes, 0)           as emprunt,
        greatest(c.recettes - c.depenses, 0)           as excedent
    from comptes as c
    left join recus as r using (pays_code, date_id, sous_secteur_code)
),
etape1_autres as (
    select a.pays_code, a.date_id, l.lecture, x.source,
        'Encaisse : ' || s.libelle_court as cible, a.sous_secteur_code, x.valeur
    from autres_et_emprunt as a
    join ss as s using (sous_secteur_code)
    cross join lectures as l
    cross join lateral (
        select 'Autres recettes (ventes, revenus du patrimoine, fonds européens…)' as source,
            a.autres_recettes as valeur
        union all
        select 'Emprunt (déficit)', a.emprunt
    ) as x
),
etape1 as (
    select pays_code, date_id, lecture, 1 as etape, source, cible, sous_secteur_code, valeur
    from prelevements
    union all
    select pays_code, date_id, lecture, 1, source, cible, sous_secteur_code, valeur
    from etape1_autres
),
entrees as (
    select pays_code, date_id, sous_secteur_code, sum(valeur) as valeur
    from etape1 where lecture = 'Par base économique' group by all
),
-- Étape 2 : ce que chaque administration garde, et ce qu'elle transfère
etape2 as (
    select e.pays_code, e.date_id, 2 as etape,
        'Encaisse : ' || s.libelle_court as source,
        'Dépense : ' || s.libelle_court as cible,
        e.sous_secteur_code,
        e.valeur - coalesce(v.valeur, 0) as valeur
    from entrees as e
    join ss as s using (sous_secteur_code)
    left join verses as v using (pays_code, date_id, sous_secteur_code)
    union all
    select t.pays_code, t.date_id, 2,
        'Encaisse : ' || sv.libelle_court,
        'Dépense : ' || sr.libelle_court,
        t.sous_secteur_versant_code,
        sum(t.valeur_meur)
    from {{ ref('fait_transferts_apu') }} as t
    join ss as sv on sv.sous_secteur_code = t.sous_secteur_versant_code
    join ss as sr on sr.sous_secteur_code = t.sous_secteur_receveur_code
    group by all
),
-- Étape 3 : dépense consolidée par fonction
depense_fonction as (
    select f.pays_code, f.date_id, f.sous_secteur_code, c.cofog_n1_libelle as fonction,
        sum(f.valeur_meur) as valeur
    from {{ ref('fait_depenses_fonction') }} as f
    join {{ ref('dim_cofog') }} as c using (cofog_code)
    group by all
),
imputation as (
    -- Éliminations par fonction imputées aux administrations versantes (ajustement RAS).
    select * from {{ ref('int_sankey__imputation_eliminations') }}
),
etape3 as (
    select d.pays_code, d.date_id, 3 as etape,
        'Dépense : ' || s.libelle_court as source,
        d.fonction as cible,
        d.sous_secteur_code,
        d.valeur + coalesce(i.elimination, 0) as valeur
    from depense_fonction as d
    join ss as s using (sous_secteur_code)
    left join imputation as i using (pays_code, date_id, fonction, sous_secteur_code)
    union all
    select a.pays_code, a.date_id, 3,
        'Dépense : ' || s.libelle_court, 'Excédent (capacité de financement)',
        a.sous_secteur_code, a.excedent
    from autres_et_emprunt as a
    join ss as s using (sous_secteur_code)
),
etapes_2_3 as (
    select x.*, l.lecture
    from (select * from etape2 union all select * from etape3) as x
    cross join lectures as l
),
annees_completes as (
    -- Uniquement les pays-années où les trois sources (prélèvements, comptes, fonctions) existent.
    select distinct pays_code, date_id from prelevements
    intersect
    select distinct pays_code, date_id from depense_fonction where sous_secteur_code in ('S1311', 'S1313', 'S1314')
    intersect
    select distinct pays_code, date_id from comptes
)
select pays_code, date_id, lecture, etape, source, cible, sous_secteur_code,
    round(sum(valeur), 3) as valeur_meur
from (
    select pays_code, date_id, lecture, etape, source, cible, sous_secteur_code, valeur from etape1
    union all
    select pays_code, date_id, lecture, etape, source, cible, sous_secteur_code, valeur from etapes_2_3
)
semi join annees_completes using (pays_code, date_id)
group by all
having abs(sum(valeur)) > 0.5
