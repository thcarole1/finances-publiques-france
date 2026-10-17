# 05 — Modèle : tables de faits

## 1. Vue d'ensemble

Le modèle est une **constellation** : plusieurs tables de faits, chacune à son propre grain,
partagent des dimensions conformes. Deux faits ne sont **jamais additionnés entre eux** : on
les compare ou on les rapporte l'un à l'autre (ex. dépenses ÷ PIB).

| # | Table | Grain | Additivité | Source principale | Lot |
|---|---|---|---|---|---|
| F01 | `Fait_Comptes_APU_Annuels` | pays × année × sous-secteur × transaction | Additive | Eurostat `gov_10a_main`, INSEE | 1 |
| F02 | `Fait_Depenses_Fonction` | pays × année × sous-secteur × COFOG × transaction | Additive | Eurostat `gov_10a_exp` | 1 |
| F03 | `Fait_Prelevements` | pays × année × sous-secteur bénéficiaire × prélèvement | Additive | Eurostat `gov_10a_taxag`, INSEE | 1 |
| F03b | `Fait_Prelevements_Fonction` | F03 × base économique (payeur) | Additive | DG TAXUD (NTL) × F03 | 1b |
| F04 | `Fait_Macro_Annuel` | pays × année | Non additive | Eurostat, OCDE | 1 |
| F05 | `Fait_Revisions` | pays × année × agrégat clé × millésime | Non additive entre millésimes | Eurostat, INSEE | 1 |
| F06 | `Fait_Transferts_APU` | pays × année × sous-secteur versant × sous-secteur receveur × transaction | Additive | INSEE | 2 |
| F07 | `Fait_Comptes_APU_Trimestriels` | pays × trimestre × sous-secteur × transaction × correction saisonnière | Additive (hors CVS/brut mélangés) | Eurostat `gov_10q_ggnfa`, INSEE | 3 |
| F08 | `Fait_Macro_Trimestriel` | pays × trimestre | Non additive | Eurostat | 3 |
| F09 | `Fait_Dette` | pays × fin d'année (fin de trimestre au lot 3b) × sous-secteur | **Semi-additive** (pas dans le temps) | Eurostat `gov_10dd_edpt1` (puis `gov_10q_ggdebt`) | 3a |
| F09b | `Fait_Dette_Instrument` | pays × fin d'année × instrument (S13 consolidé) | Semi-additive | Eurostat `gov_10dd_edpt1` | 3a |
| F10 | `Fait_Detention_Dette` | pays × fin d'année × détenteur (S13 consolidé) | Semi-additive | Eurostat `gov_10dd_ggd` | 3a |
| F11 | `Fait_Dette_Titres` | date d'instantané × titre (ISIN) | Semi-additive | AFT | 3 |
| F12 | `Fait_Taux_Marche` | pays × fin de mois × maturité | Non additive | Eurostat `irt_lt_mcby_m` (puis BCE, OCDE) | 3a |
| F13 | `Fait_Hypotheses` | scénario × millésime × pays × année cible × variable | Non additive | Référentiel prévisions, AMECO, FMI, scénarios YAML | 4 |
| F14 | `Fait_Projections` | scénario × pays × année × indicateur projeté | Non additive pour les ratios | Moteur de projection (Python) | 4 |
| F15 | `Fait_Redistribution` | année × décile × flux × approche × ménage type | Additive pour les montants totaux | INSEE, DREES | 5 |
| F16 | `Fait_Budget_Etat` | exercice × action LOLF × titre × stade × type de crédit | Additive à stade et type de crédit fixés | Direction du budget, DGFiP | 6 |
| F17 | `Fait_Budget_Secu` | exercice × branche × sous-objectif ONDAM × stade × poste | Additive à stade fixé | Sécurité sociale | 6 |
| F18 | `Fait_Comptes_Locaux` | exercice × collectivité × agrégat local | Additive (non consolidée) | OFGL | 7 |
| F19 | `Fait_Fiscalite_Locale` | année × commune × taxe × collectivité bénéficiaire | Bases et produits additifs, taux non additifs | DGFiP (REI) | 7 |
| F20 | `Fait_Population_Locale` | année × commune | Additive entre communes | INSEE | 7 |

Tables de présentation (dérivées, recalculées par le pipeline, jamais sources de vérité) :

| Table | Rôle |
|---|---|
| `Pres_Flux_Sankey` | Nœuds et flux pré-calculés pour le Sankey *prélèvements → administration qui encaisse → administration qui dépense → fonction* |

## 2. Colonnes communes à toutes les tables de faits

| Colonne | Rôle |
|---|---|
| `date_id` | Clé vers `Dim_Date` (convention de fin de période) |
| `pays_code` | Clé vers `Dim_Pays` (sauf faits purement français, où elle vaut `FR`) |
| `source_id` | Clé vers `Dim_Source` |
| `millesime_id` | Clé vers `Dim_Millesime` (traçabilité) |
| `statut_valeur` | `DEFINITIF`, `SEMI_DEFINITIF`, `PROVISOIRE`, `ESTIME` (indicateurs de qualité des producteurs, ex. drapeaux Eurostat) |

Les attributs à très faible cardinalité propres à un seul fait (`type_credit`, `poste`,
`correction`, `perimetre`, `type_valeur`) restent des **dimensions dégénérées** : de simples
colonnes du fait, sans table de dimension.

**Montants** : stockés en **millions d'euros** (`valeur_meur`) et en **millions de monnaie
nationale** (`valeur_mnac`) pour les pays hors zone euro. Conversion : taux de change **moyen**
de l'année pour les flux, taux de **fin de période** pour les stocks. Les ratios (% du PIB,
par habitant, en SPA) sont calculés en DAX, jamais stockés, sauf dans les faits d'hypothèses et
de projections où ils sont la donnée elle-même.

## 3. Détail des tables

### F01 — `Fait_Comptes_APU_Annuels`

- **Clés** : `pays_code`, `date_id`, `sous_secteur_code`, `transaction_code`, `millesime_id`.
- **Valeurs** : `valeur_meur`, `valeur_mnac`.
- **Contenu** : les **feuilles** de recettes et de dépenses (voir `Dim_Transaction`), pour
  chaque sous-secteur, plus les lignes `S13_ELIM`. Le solde se calcule (recettes − dépenses).
- **Couverture** : UE27 + agrégats depuis 1995 ; pays OCDE au lot 8.
- **Règle** : la somme des feuilles = total publié (contrôle QC-B03).

### F02 — `Fait_Depenses_Fonction`

- **Clés** : `pays_code`, `date_id`, `sous_secteur_code`, `cofog_code` (feuille), `transaction_code` (feuille de dépense).
- **Contenu** : croisement complet COFOG niveau 2 × nature, avec feuilles « non ventilé ».
- **Règle** : pour un pays, une année et un sous-secteur, la somme sur toutes les fonctions est
  égale aux dépenses totales de F01 (QC-B04).
- **Volume** : ~30 pays × 30 ans × 6 sous-secteurs × ~80 fonctions × ~10 natures ≈ 4 à 5 millions
  de lignes au maximum (en pratique beaucoup moins, car le croisement est creux).

### F03 — `Fait_Prelevements`

- **Clés** : `pays_code`, `date_id`, `sous_secteur_code` (bénéficiaire), `prelevement_code`.
- **Valeurs** : `valeur_meur`, `valeur_mnac`.
- **Lien payeur** : via le pont pondéré `Map_Prelevement_Payeur` (voir `04` et `06`), sans
  relation bidirectionnelle.
- **Note** : la ventilation par sous-secteur bénéficiaire répond à « qui encaisse quoi ? »
  (ex. la part de TVA affectée à la Sécurité sociale et aux collectivités).

### F04 — `Fait_Macro_Annuel` (format large)

`pib_meur`, `pib_mnac`, `pib_volume_indice`, `deflateur_pib`, `pib_spa`, `population`,
`inflation_ipch`, `taux_change_moyen`, `taux_change_fin`, `ppa_eur`. Sert de dénominateur à
toutes les mesures en % du PIB, par habitant et en SPA.

### F05 — `Fait_Revisions`

- **Clés** : `pays_code`, `date_id`, `indicateur_code` (vers `Dim_Indicateur`), `millesime_id`.
- **Grain** : pays × année × agrégat clé × **millésime** (tous les millésimes conservés).
- **Agrégats** : solde public, dette, dépenses totales, recettes totales, PIB (S13 uniquement).
- **Usage** : voir comment un chiffre a été révisé au fil des publications (« le déficit 2023 vu
  en avril 2024, puis en octobre 2024… »).

### F06 — `Fait_Transferts_APU`

- **Clés** : `pays_code`, `date_id`, `sous_secteur_versant_code`, `sous_secteur_receveur_code`,
  `transaction_code` (D73 transferts courants entre administrations, D92 aides à
  l'investissement, D99 autres transferts en capital, impôts affectés…).
- **Rôle double de `Dim_Sous_Secteur`** : une copie `Dim_Sous_Secteur_Receveur` (table calculée)
  pour garder des relations actives, simples et lisibles dans le Sankey.
- **Règle** : la somme des transferts reçus et versés est cohérente avec les lignes `S13_ELIM`
  de F01 (QC-B05, avec tolérance documentée car les sources diffèrent).

### F07 — `Fait_Comptes_APU_Trimestriels`

- **Clés** : comme F01, au grain trimestriel, plus `correction` (`BRUT`, `CVS`).
- **Règle** : en brut, la somme des quatre trimestres est égale à l'année de F01, au même
  millésime et à la révision près (QC-A07, avertissement).
- **Profondeur** : à partir de 2000 (décision D9).

### F09 — `Fait_Dette`

> **Mise en œuvre (lot 3a).** Eurostat ne croise pas sous-secteur et instrument : la dette par
> instrument n'existe que pour l'ensemble consolidé (S13). F09 porte donc le sous-secteur, et
> F09b (`Fait_Dette_Instrument`) l'instrument ; la durée à l'origine (court / long terme) est un
> attribut de `Dim_Instrument_Dette` (court terme = dépôts + titres et prêts de court terme, ce qui
> reproduit exactement la ventilation « 1 an ou moins » d'Eurostat). QC-B13 vérifie que les trois
> tables de dette donnent le même total.

- **Clés** : `pays_code`, `date_id` (fin de trimestre), `sous_secteur_code`, `instrument_code`, `maturite_code`.
- **Valeur** : encours nominal en M€ (dette au sens de Maastricht : brute, consolidée, valeur nominale).
- **Consolidation** : même mécanisme `S13_ELIM` que F01 (la dette d'un sous-secteur détenue par
  un autre est éliminée au niveau S13).
- **Semi-additivité** : on additionne entre sous-secteurs et instruments, jamais entre dates.
- **Règle** : la valeur au T4 est égale à la dette annuelle notifiée (QC-B06).

### F10 — `Fait_Detention_Dette`

Part et montant de la dette détenus par catégorie de détenteur (non-résidents, banque centrale,
établissements de crédit, assurances…). Le périmètre (dette négociable de l'État ou dette de
Maastricht) est porté par une colonne `perimetre`.

> **Mise en œuvre (lot 3a).** Source Eurostat `gov_10dd_ggd` (dette de Maastricht consolidée, tous
> pays européens) plutôt que l'AFT, dont le site refuse les accès automatisés. Feuilles exhaustives :
> `S1_NV` (autres résidents) et `NV` complètent le total. Détail publié depuis 2020 pour la plupart
> des pays (depuis 1995 pour l'Allemagne, la Belgique, les Pays-Bas…).

### F11 — `Fait_Dette_Titres` (échéancier AFT)

> **Reporté.** Le site de l'AFT bloque les accès automatisés depuis la session (page de
> vérification anti-robot) ; un essai depuis GitHub Actions reste à faire. Eurostat ne publie pas de ventilation par durée restante
> pour la France. À reprendre si un fichier de l'AFT peut être déposé manuellement dans le dépôt.

- **Clés** : `date_id` (date de l'instantané, fin de mois), `isin`.
- **Valeurs** : `encours_nominal_meur`, `encours_indexe_meur` (y compris le supplément
  d'indexation des titres indexés sur l'inflation).
- **Échéancier** : la date d'échéance est un attribut de `Dim_Titre`, également exposée comme
  `date_echeance_id` avec une **relation inactive** vers `Dim_Date` (activée par
  `USERELATIONSHIP` dans les mesures d'échéancier).
- **Règle** : la somme des encours par titre est égale à l'encours total publié par l'AFT (QC-B07).

### F12 — `Fait_Taux_Marche`

Rendements souverains de fin de mois (ou moyenne mensuelle, colonne `type_valeur`) par pays et
maturité. L'écart avec l'Allemagne (*spread*) est calculé en DAX.

### F13 — `Fait_Hypotheses`

- **Clés** : `scenario_id`, `millesime_id` (date de publication de la trajectoire), `pays_code`,
  `date_id` (année cible), `variable_code`.
- **Valeur** : `valeur` (en % ou % du PIB selon `Dim_Variable_Hypothese.unite`).
- **Horizon** : `annee_cible − annee_publication` est calculé pour l'analyse des erreurs de
  prévision par horizon (prévision pour l'année même, l'année suivante, à 2 ans…).
- **Contenu** : trajectoires officielles (tous millésimes) + scénarios personnels (`scenarios/*.yml`).

### F14 — `Fait_Projections`

- **Clés** : `scenario_id`, `pays_code`, `date_id`, `indicateur_code` (vers `Dim_Indicateur`).
- **Indicateurs** : dette (M€ et % du PIB), charge d'intérêts, taux apparent, solde, solde
  primaire, effet boule de neige, besoin de financement, montant refinancé.
- **Production** : calculée par `projection/` en Python à partir de F13 et de l'échéancier F11
  (voir `08`). Les curseurs en direct du rapport n'écrivent pas ici : ils sont calculés en DAX.

### F15 — `Fait_Redistribution`

- **Clés** : `date_id`, `decile_code`, `flux_code`, `approche_code`, `menage_type_code`
  (`_NA` tant qu'OpenFisca n'est pas intégré).
- **Valeurs** : `montant_total_meur` (additif), `montant_moyen_uc_eur` (moyen par unité de
  consommation, non additif entre déciles), `part_revenu_initial` (%).
- **Avertissement** : les deux approches ne portent pas sur les mêmes années ni exactement sur
  les mêmes conventions ; le rapport les compare côte à côte, sans les additionner.

### F16 — `Fait_Budget_Etat`

- **Clés** : `date_id` (exercice), `action_code`, `titre_code`, `stade_code`, `type_credit`
  (`AE` autorisations d'engagement / `CP` crédits de paiement).
- **Règle** : les mesures imposent un stade et un type de crédit (pas de somme LFI + exécution).
- **Écarts** : taux d'exécution = exécuté ÷ LFI ; écart voté-exécuté.
- **Correspondance COFOG** : via `Map_LOLF_COFOG`, indicative.

### F17 — `Fait_Budget_Secu`

- **Clés** : `date_id`, `branche_code`, `ondam_sous_objectif_code` (`_NA` hors ONDAM),
  `stade_code`, `poste` (`CHARGES`, `PRODUITS`).
- Le solde par branche est calculé (produits − charges).

### F18 — `Fait_Comptes_Locaux`

- **Clés** : `date_id` (exercice), `collectivite_id`, `agregat_local_code`.
- **Valeur** : `montant_eur`.
- **Attention** : les comptes locaux sont **non consolidés** entre collectivités (une dotation
  d'un EPCI à ses communes apparaît des deux côtés) ; le rapport le signale. La vue consolidée
  des administrations locales est celle de F01 (S1313).

### F19 — `Fait_Fiscalite_Locale`

- **Clés** : `date_id`, `geo_code` (commune), `taxe_code`, `collectivite_beneficiaire_id`.
- **Valeurs** : `base_nette_eur`, `taux_vote` (%), `produit_eur`.
- **Règle** : taux moyen pondéré = Σ produits ÷ Σ bases (jamais une moyenne simple des taux).

### F20 — `Fait_Population_Locale`

Population municipale par commune et par année, exprimée dans la géographie en vigueur via
`Map_COG_Passage`. Dénominateur des montants par habitant locaux.

## 4. Relations

- Toutes les relations : **plusieurs-à-un**, **filtrage simple** (dimension → fait).
- **Aucune relation bidirectionnelle.** Les ponts (`Map_Prelevement_Payeur`, `Map_LOLF_COFOG`,
  `Map_COG_Passage`) sont exploités dans les mesures (`TREATAS`, `SUMX` pondéré) ou appliqués
  en amont dans le pipeline.
- Relations inactives documentées : `Fait_Dette_Titres[date_echeance_id] → Dim_Date`.
- Faits purement français (F10, F11, F15 à F20) : reliés à `Dim_Pays` par une colonne
  `pays_code = 'FR'` pour que les filtres de pays restent cohérents dans tout le rapport.

## 5. Volumétrie estimée

| Groupe | Lignes estimées | Commentaire |
|---|---|---|
| F01–F05 | < 2 M | Dominé par F02 |
| F06–F12 | < 1 M | |
| F13–F17 | < 0,5 M | |
| F18–F20 | 5–20 M **[À confirmer]** | ~35 000 communes × ~25 ans × agrégats et taxes |

Le total reste compatible avec le mode Import d'un poste de travail (quelques centaines de Mo en
mémoire au maximum). Si nécessaire, F18–F19 pourront démarrer à une année plus récente (décision D6).
