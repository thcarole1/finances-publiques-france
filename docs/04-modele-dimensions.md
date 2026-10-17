# 04 — Modèle : dimensions

## 1. Principes

- **Dimensions conformes** : une dimension est partagée par toutes les tables de faits qui
  l'utilisent (ex. `Dim_Pays`, `Dim_Date`, `Dim_Sous_Secteur`, `Dim_Millesime`).
- **Clés naturelles** stables et lisibles (codes officiels : SEC, COFOG, ISO, COG…), en texte,
  sauf `Dim_Date` (entier `AAAAMMJJ`). Le volume des dimensions rend le gain des clés de
  substitution négligeable, et les clés naturelles simplifient le débogage et les jointures.
- **Membre « inconnu »** dans chaque dimension (`code = '_NA'`, libellé « Non renseigné ») pour
  ne jamais perdre une ligne de fait sur une clé manquante.
- **Libellés en français**, codes d'origine conservés dans une colonne `code_source` quand ils
  diffèrent (ex. codes Eurostat `EL` pour la Grèce).
- Chaque dimension a une colonne `ordre_tri` pour un tri métier explicite dans les visuels.
- Les colonnes `definition_courte` et `glossaire_id` relient les membres au glossaire pédagogique.

## 2. Dimensions transverses

### `Dim_Date` — table de dates (marquée comme telle)

| Colonne | Type | Exemple | Note |
|---|---|---|---|
| `date_id` | int | 20251231 | Clé |
| `date` | date | 2025-12-31 | |
| `annee`, `trimestre`, `mois` | int | 2025, 4, 12 | |
| `annee_trimestre` | texte | 2025-T4 | |
| `est_fin_annee`, `est_fin_trimestre`, `est_fin_mois` | bool | | Filtres pour les grains |
| `decennie` | texte | 2020s | |
| `periode_historique` | texte | Crise sanitaire | Repères : 2008-09, 2020-21, 2022-23… |

- Plage : **1990-01-01 → 2075-12-31** (l'échéancier des OAT va au-delà de 2070).
- Convention de rattachement : un fait **annuel** est daté du **31/12**, un fait **trimestriel**
  du dernier jour du trimestre, un fait **mensuel** du dernier jour du mois. Les mesures
  vérifient le grain affiché (voir `06`).

### `Dim_Pays`

| Colonne | Exemple | Note |
|---|---|---|
| `pays_code` | FR | Clé : ISO 3166-1 alpha-2 (Grèce = GR, Royaume-Uni = GB) |
| `code_eurostat` | EL | Correspondance Eurostat |
| `code_iso3` | FRA | Correspondance OCDE, FMI |
| `libelle` | France | |
| `type` | Pays / Agrégat | `EU27_2020`, `EA20` sont des agrégats |
| `est_ue`, `est_zone_euro`, `est_ocde` | bool | |
| `groupe_comparaison` | Grands voisins | Préréglages de sélection |
| `devise` | EUR | |
| `est_federal` | bool | Indique l'existence du sous-secteur S1312 |
| `source_reference` | Eurostat / OCDE | Hiérarchie des sources |
| `niveau_comparabilite` | Élevé / Moyen | Avertissement affiché pour les pays hors UE |
| `note_comparabilite` | « Santé largement privée… » | Texte pédagogique |

Pays OCDE hors UE proposés : États-Unis, Royaume-Uni, Japon, Canada, Suisse, Norvège, Australie,
Corée du Sud (décision D4, validée).

### `Dim_Source`

`source_id`, `producteur`, `jeu_donnees`, `url`, `licence`, `libelle_attribution`, `frequence`,
`niveau_reference` (référence / contrôle).

### `Dim_Millesime`

| Colonne | Exemple | Note |
|---|---|---|
| `millesime_id` | EUROSTAT_GOV10A_2026-04-22 | Clé |
| `source_id` | EUROSTAT_GOV10A | |
| `date_publication` | 2026-04-22 | Date du producteur, sinon date de collecte |
| `date_collecte` | 2026-04-23 | |
| `libelle` | Notification d'avril 2026 | |
| `rang_recence` | 1 | 1 = dernier millésime de la source |
| `est_dernier` | bool | Filtre par défaut |
| `base_comptable` | Base 2020 | Changement de base INSEE |

### `Dim_Scenario`

| Colonne | Exemple | Note |
|---|---|---|
| `scenario_id` | REEL | Clé |
| `libelle` | Données observées | |
| `type` | REEL / OFFICIEL / PERSONNEL / PROJECTION | |
| `institution` | Gouvernement, HCFP, Commission, FMI, OCDE, Banque de France, Personnel | |
| `scenario_base_id` | GOUV_PLF_2026 | Trajectoire dont part un scénario personnel |
| `date_publication` | 2025-10-14 | Pour les trajectoires officielles |
| `description`, `auteur`, `fichier` | | Pour les scénarios personnels (`scenarios/*.yml`) |

## 3. Comptabilité nationale

### `Dim_Sous_Secteur`

| `sous_secteur_code` | Libellé | Niveau | Parent | Note |
|---|---|---|---|---|
| S13 | Administrations publiques | 0 | — | Total consolidé |
| S1311 | Administration centrale | 1 | S13 | En France : État + organismes divers (ODAC) |
| S1312 | États fédérés | 1 | S13 | Allemagne, Autriche, Belgique, Espagne… ; vide pour la France |
| S1313 | Administrations locales | 1 | S13 | APUL : collectivités + organismes locaux |
| S1314 | Administrations de sécurité sociale | 1 | S13 | ASSO : régimes de base, Unédic, complémentaires, hôpitaux… |
| **S13_ELIM** | Transferts internes (éliminés) | 1 | S13 | **Écritures d'élimination**, voir ci-dessous |
| S1311_ETAT, S1311_ODAC, … | Détail France | 2 | S1311… | Optionnel, source INSEE |

**Mécanisme de consolidation.** Les faits stockent pour chaque sous-secteur sa valeur
*consolidée à l'intérieur du sous-secteur* (convention de publication d'Eurostat **[À confirmer]**
au lot 2 jeu par jeu), plus une ligne `S13_ELIM` égale à
`S13 publié − Σ sous-secteurs`. Ainsi :

- **somme de tous les membres = S13 consolidé** (vue consolidée, celle d'Eurostat) ;
- **somme sans `S13_ELIM` = vue non consolidée** (ce que chaque acteur dépense, transferts compris) ;
- la ligne `S13_ELIM` est elle-même lisible et pédagogique : « X milliards circulent entre
  administrations et ne sont comptés qu'une fois ».

La bascule consolidé / non consolidé est un simple filtre sur l'attribut `est_elimination`,
piloté par un groupe de calcul (voir `06`). Aucune mesure ne peut additionner S13 et ses
sous-secteurs, puisque S13 n'est pas stocké comme ligne de fait.

### `Dim_Transaction` — nature économique (SEC 2010)

| Colonne | Exemple |
|---|---|
| `transaction_code` | D1 |
| `libelle` | Rémunération des salariés |
| `libelle_court` | Masse salariale |
| `sens` | Dépense / Recette |
| `groupe_presentation` | Fonctionnement / Prestations / Investissement / Intérêts / Transferts… |
| `parent_code`, `niveau` | OTE, 1 |
| `definition_courte` | Salaires et cotisations des agents publics |

**Règle d'additivité.** Les faits ne stockent que des **feuilles** formant une décomposition
**exhaustive** des totaux (dépenses totales `OTE`, recettes totales `TR`). Une feuille
« Autres » absorbe le résidu, calculé en transformation, pour que la somme des feuilles soit
**exactement** égale au total publié. Les totaux officiels sont conservés à part, uniquement
pour les contrôles qualité.

Feuilles de dépense : consommation intermédiaire (P2), rémunération des salariés (D1),
subventions (D3), intérêts (D41), prestations sociales en espèces (D62), prestations sociales
en nature achetées (D632), autres transferts courants (D7), formation brute de capital (P5),
transferts en capital (D9), autres dépenses (résidu).

Feuilles de recette : impôts sur la production et les importations (D2), impôts courants sur le
revenu et le patrimoine (D5), impôts en capital (D91), cotisations sociales nettes (D61),
production marchande et pour usage final propre (P11 + P12 + P131), revenus de la propriété
(D4), autres transferts reçus (D7 + D9 hors D91), autres recettes (résidu).

### `Dim_COFOG` — fonctions des administrations

| Colonne | Exemple |
|---|---|
| `cofog_code` | GF1002 |
| `cofog_n1_code`, `cofog_n1_libelle` | GF10, Protection sociale |
| `cofog_n2_code`, `cofog_n2_libelle` | GF1002, Vieillesse |
| `niveau` | 2 |
| `est_non_ventile` | bool |

Feuilles stockées : les sous-fonctions de niveau 2 + une feuille `GFxx_NV` (« non ventilé »)
par fonction de niveau 1 quand la somme du niveau 2 ne couvre pas le niveau 1 (fréquent pour les
pays hors UE ou les années anciennes).

## 4. Recettes et payeurs

### `Dim_Prelevement` — type de prélèvement

| Colonne | Exemple |
|---|---|
| `prelevement_code` | D211 |
| `libelle` | TVA |
| `categorie_sec` | Impôts sur la production et les importations |
| `categorie_pedagogique` | Impôts sur la consommation / sur le travail / sur le capital / sur le patrimoine |
| `est_prelevement_obligatoire` | bool |
| `libelle_national` | Taxe sur la valeur ajoutée |

### `Dim_Payeur`

| `payeur_code` | Libellé | Groupe |
|---|---|---|
| MEN_CONSO | Ménages, en tant que consommateurs | Ménages |
| MEN_ACTIF | Ménages, sur les revenus d'activité | Ménages |
| MEN_REMPL | Ménages, sur les revenus de remplacement (retraites, chômage) | Ménages |
| MEN_CAPITAL | Ménages, sur les revenus du capital et le patrimoine | Ménages |
| ENT | Entreprises | Entreprises |
| EMP_PUB | Administrations, en tant qu'employeur | Administrations |
| RDM | Non-résidents | Reste du monde |
| _NA | Non ventilé | — |

### `Map_Prelevement_Payeur` — table de répartition (pont pondéré)

| `prelevement_code` | `payeur_code` | `convention_id` | `coefficient` | `justification` |
|---|---|---|---|---|
| D211 | MEN_CONSO | LEGALE | *à calibrer* | Part de la TVA acquittée sur la consommation finale des ménages (le reste : APU, logement, entreprises non assujetties) **[À confirmer]** |
| … | | | | |

- Référentiel versionné : `data/reference/map_prelevement_payeur.csv`.
- **La somme des coefficients vaut 1** par prélèvement et par convention (contrôle bloquant).
- `Dim_Convention_Incidence` : `LEGALE` (qui verse, par défaut) et `ECONOMIQUE` (qui supporte,
  hypothèses documentées et modifiables). C'est l'application directe de la notion d'incidence
  fiscale : changer de convention change la réponse à « qui paie ? ».

## 5. Redistribution

- `Dim_Decile` : D1 à D10 + `ENS` (ensemble), avec bornes de niveau de vie si disponibles.
- `Dim_Flux_Redistribution` : `flux_code`, `libelle`, `type` (prélèvement / prestation / service
  public), `sous_type` (impôt sur le revenu, CSG, TVA, prestations familiales, minima sociaux,
  aides au logement, éducation, santé…), `signe` (−1 pour un prélèvement, +1 pour un bénéfice).
- `Dim_Approche_Redistribution` : `MONETAIRE`, `ELARGIE`.
- `Dim_Menage_Type` *(préparée, alimentée avec OpenFisca plus tard)* : composition familiale,
  nombre d'enfants, statut d'activité, tranche de revenu, statut d'occupation du logement.

## 6. Dette et taux

- `Dim_Instrument_Dette` : numéraire et dépôts (F2), titres de créance à court terme (F31),
  à long terme (F32), crédits (F4).
- `Dim_Maturite` : court terme (≤ 1 an), long terme, et tranches d'échéance résiduelle.
- `Dim_Detenteur` : résidents (banque centrale, banques, assurances, autres) / non-résidents.
- `Dim_Titre` *(dette négociable de l'État, AFT)* : `isin`, `type` (BTF, OAT, OATi, OAT€i,
  OAT verte), `coupon`, `date_emission`, `date_echeance`, `indexation` (aucune, inflation France,
  inflation zone euro).
- `Dim_Maturite_Taux` : 3 mois, 2 ans, 5 ans, 10 ans, 30 ans.

## 7. Budgets votés

- `Dim_LOLF` : hiérarchie mission → programme → action, avec `est_mission_budget_general`,
  et dates de validité (la maquette budgétaire change d'une année sur l'autre).
- `Dim_Titre_Budgetaire` : titres 1 à 7 (dépenses de personnel, de fonctionnement, charge de la
  dette, d'investissement, d'intervention, d'opérations financières…).
- `Dim_Stade_Budgetaire` : PLF, LFI, LFR, Exécution ; PLFSS, LFSS initiale, LFSS rectificative,
  Réalisé.
- `Dim_Branche_Secu` : branche (maladie, AT-MP, vieillesse, famille, autonomie), périmètre
  (régime général, ROBSS), sous-objectif ONDAM.
- `Map_LOLF_COFOG` : correspondance **indicative** programme → fonction COFOG, avec
  `coefficient` et `niveau_confiance` ; le rapport la signale comme approximative.

## 8. Collectivités et géographie

- `Dim_Geographie` : une ligne par **commune** (code COG en vigueur), avec la hiérarchie
  commune → intercommunalité (EPCI) → département → région, population légale, strate de
  population, type (urbain/rural).
- `Map_COG_Passage` : table de passage `code_commune_historique → code_commune_actuel`
  (avec `annee` et `coefficient` en cas de scission) pour exprimer les séries anciennes
  dans la géographie actuelle.
- `Dim_Collectivite` : une ligne par **entité budgétaire** (commune, EPCI, département,
  région, collectivité à statut particulier), clé SIREN, `type`, `libelle`, et `geo_code`
  du territoire de rattachement (commune pour une commune, chef-lieu sinon).
- `Dim_Agregat_Local` : agrégats financiers normalisés de l'OFGL (recettes et dépenses de
  fonctionnement, épargne brute, dépenses d'équipement, encours de dette…).
- `Dim_Taxe_Locale` : taxe foncière bâti (TFPB), non bâti (TFPNB), taxe d'habitation sur les
  résidences secondaires (THRS), cotisation foncière des entreprises (CFE)…, avec le niveau
  bénéficiaire (commune, EPCI…).

## 9. Hypothèses, pédagogie et tables techniques

- `Dim_Variable_Hypothese` : croissance du PIB en volume, déflateur du PIB, inflation, taux à
  10 ans, taux apparent de la dette, solde primaire, dépense publique, prélèvements obligatoires,
  ajustement stock-flux ; avec `unite` (% ou % du PIB).
- `Dim_Indicateur` : liste des indicateurs du rapport (code, libellé, mesure DAX associée,
  unité, sens souhaitable, `glossaire_id`) ; alimente les paramètres de champ et les info-bulles,
  et sert de clé `indicateur_code` dans `Fait_Revisions` (F05) et `Fait_Projections` (F14).
- `Dim_Glossaire` : `glossaire_id`, `terme`, `definition_courte` (info-bulle), `definition_longue`
  (encadré « Comprendre »), `exemple`, `pour_aller_plus_loin` (URL). Généré depuis
  `docs/glossaire.md`.
- Tables **déconnectées** : `Param_Unite`, paramètres What-if (`Param_*`), voir `06` et `08`.
