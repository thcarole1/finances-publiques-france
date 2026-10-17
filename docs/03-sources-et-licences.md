# 03 — Sources et licences

Les codes de jeux de données marqués **[À confirmer]** seront vérifiés lors de l'exploration de
la source, au lot indiqué. Chaque source fera l'objet d'une fiche détaillée
(`docs/sources/<source>.md`) au moment de son intégration.

## 1. Principe de hiérarchie des sources

Quand un même chiffre existe dans plusieurs sources :

1. **France** : l'**INSEE** fait référence (comptes nationaux, notification de déficit et dette).
   Eurostat sert de contrôle de cohérence (même chiffre attendu, à la révision près).
2. **Pays de l'UE** : **Eurostat**, définitions harmonisées SEC 2010.
3. **Pays OCDE hors UE** : **OCDE**, avec un indicateur de comparabilité (voir `Dim_Pays`).
4. **Données de gestion** (budgets votés, dette négociable, collectivités) : producteur
   administratif (DGFiP, Direction du budget, AFT, OFGL, Sécurité sociale).

## 2. Catalogue

### Comptabilité nationale et agrégats

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| Eurostat | `gov_10a_main` | Principaux agrégats des APU par sous-secteur (recettes, dépenses, solde) | Annuelle | API SDMX | 1 |
| Eurostat | `gov_10a_exp` | Dépenses par fonction COFOG (2 niveaux) × transaction SEC | Annuelle | API SDMX | 1 |
| Eurostat | `gov_10a_taxag` | Recettes fiscales et cotisations détaillées par type d'impôt | Annuelle | API SDMX | 1 |
| Eurostat | `gov_10q_ggnfa` | Comptes non financiers trimestriels des APU | Trimestrielle | API SDMX | 3 |
| Eurostat | `gov_10q_ggdebt` | Dette trimestrielle par sous-secteur, instrument, maturité | Trimestrielle | API SDMX | 3 |
| Eurostat | `gov_10dd_edpt1` | Notification de déficit et dette (procédure de déficit excessif), dette par instrument | Semestrielle | API SDMX | 3a |
| Eurostat | `nama_10_gdp`, `namq_10_gdp`, `demo_pjan`, `prc_hicp_aind`, `prc_ppp_ind`, `ert_bil_eur_a` | PIB annuel et trimestriel, population, inflation, parités de pouvoir d'achat, taux de change | Variable | API SDMX | 1 |
| INSEE | Comptes nationaux annuels, compte des APU (tableaux 3.xxx) | Comptes détaillés par sous-secteur (État, ODAC, APUL, ASSO), **transferts entre sous-secteurs** | Annuelle (fin mai) | Fichiers + API BDM **[À confirmer]** | 1–2 |
| INSEE | Dette trimestrielle de Maastricht (`DETTE-TRIM-APU-2020`), dette négociable de l'État (`DETTE-NEGOCIABLE-ETAT`) | Dette par administration (État, organismes, collectivités, Sécurité sociale) ; encours de l'État par durée et type de taux | Trimestrielle / mensuelle | API BDM (SDMX, publique) | 3b |
| INSEE | Taux de prélèvements obligatoires | Définition française des PO | Annuelle | Fichiers | 1 |
| OCDE | Comptes nationaux des APU (COFOG, déficit, dette), *Revenue Statistics* | Pays hors UE | Annuelle | API SDMX | 8 |

### Fiscalité par base économique

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| Commission européenne, DG TAXUD | Listes nationales des impôts (*National Tax Lists*) | Chaque impôt national, son code SEC, sa base économique ; répartition de l'impôt sur le revenu | Annuelle (fin mars) | XLSX | 1b |

### Dette et taux

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| AFT | Bulletin mensuel, encours de la dette négociable, détail des titres | Encours par titre (OAT, OATi, OAT€i, BTF), coupons, échéances | Mensuelle | Fichiers XLSX/CSV | 3 |
| AFT | Détention de la dette négociable par les non-résidents | Part détenue par les non-résidents | Trimestrielle | Fichiers | 3 |
| Banque de France | Webstat | Détenteurs, taux d'émission | Mensuelle | API (clé) **[À confirmer]** | 3 |
| BCE | Data Portal, flux YC | Courbe des taux des emprunts d'État de la zone euro (AAA et ensemble), 1 à 30 ans | Quotidienne | API SDMX | 3b |
| Eurostat | `gov_10q_ggdebt`, `gov_10q_ggnfa`, `namq_10_gdp` | Dette, comptes et PIB trimestriels | Trimestrielle | API SDMX | 3b |
| Eurostat | `irt_lt_mcby_m` | Taux d'intérêt à long terme (critère de convergence), tous pays UE | Mensuelle | API SDMX | 3a |
| Eurostat | `gov_10dd_ggd` | Dette publique par détenteur (résidents par catégorie, non-résidents) | Annuelle | API SDMX | 3a |
| OCDE | Taux d'intérêt à long terme | Pays hors UE | Mensuelle | API SDMX | 8 |

### Budgets votés et exécutés

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| Direction du budget / data.economie.gouv.fr | PLF, LFI : crédits par mission, programme, action, titre | Budget voté de l'État (AE et CP) | Annuelle | API Opendatasoft / CSV | 6 |
| Direction du budget / DGFiP | Exécution du budget de l'État, situation mensuelle budgétaire | Budget exécuté | Annuelle / mensuelle | CSV | 6 |
| Sécurité sociale (CCSS, annexes LFSS) | Charges, produits et soldes par branche ; ONDAM et sous-objectifs | Voté et réalisé | Annuelle | XLSX / PDF **[À confirmer]** | 6 |

### Collectivités locales

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| OFGL | Comptes des communes, groupements à fiscalité propre, départements, régions | Agrégats financiers par collectivité | Annuelle | API Opendatasoft (data.ofgl.fr) | 7 |
| DGFiP | Fichier REI (recensement des éléments d'imposition) | Taux, bases et produits des impôts locaux par commune | Annuelle | data.gouv.fr | 7 |
| INSEE | Code officiel géographique (COG) et tables de passage | Communes, fusions, rattachements | Annuelle | Fichiers | 7 |
| INSEE / DGCL | Population légale, intercommunalités | Population et rattachements | Annuelle | Fichiers | 7 |

### Redistribution

| Source | Jeu de données | Contenu | Fréquence | Accès | Lot |
|---|---|---|---|---|---|
| INSEE / DREES (*France, portrait social* ; modèle Ines) | Redistribution monétaire par décile de niveau de vie | Prélèvements directs et prestations par décile | Annuelle | XLSX | 5 |
| INSEE | Redistribution élargie (études ponctuelles) | Impôts indirects et services publics individualisables par décile | Ponctuelle **[À confirmer]** | XLSX | 5 |

### Prévisions et trajectoires

| Source | Jeu de données | Contenu | Fréquence | Lot |
|---|---|---|---|---|
| Gouvernement | Rapport économique, social et financier (PLF), plan budgétaire et structurel de moyen terme et rapports d'avancement | Trajectoire officielle | Annuelle | 4 |
| HCFP | Avis sur les prévisions | Appréciation (qualitative + chiffres cités) | Annuelle | 4 |
| Commission européenne | Prévisions économiques, base **AMECO** | Prévisions par pays, **millésimes conservés** | Semestrielle | 4 |
| FMI | *World Economic Outlook* (avril, octobre) | Prévisions par pays, **millésimes historiques disponibles** | Semestrielle | 4 |
| OCDE | *Economic Outlook* | Prévisions par pays | Semestrielle | 4 |
| Banque de France | Projections macroéconomiques | Croissance, inflation | Trimestrielle | 4 |

Les prévisions du gouvernement et du HCFP sont publiées dans des documents (PDF). Elles seront
saisies dans des **référentiels versionnés** (`data/reference/previsions_officielles.csv`),
avec la référence précise du document et de la page. C'est un travail manuel, limité aux
quelques variables clés (croissance, inflation, solde, dette, dépense).

## 3. Licences et attribution

| Producteur | Licence | Attribution requise |
|---|---|---|
| INSEE, DGFiP, Direction du budget, AFT, OFGL, Sécurité sociale (data.gouv.fr) | **Licence Ouverte / Open Licence 2.0 (Etalab)** | Oui : producteur + date de mise à jour |
| Eurostat, Commission européenne (AMECO) | Politique de réutilisation de la Commission (décision 2011/833/UE) | Oui : « Source : Eurostat » |
| OCDE | **CC BY 4.0** | Oui |
| BCE | Réutilisation autorisée avec citation de la source | Oui |
| FMI | Conditions d'utilisation des données du FMI **[À confirmer]** | Oui |
| Banque de France | Conditions de réutilisation Webstat **[À confirmer]** | Oui |

Mise en œuvre :

- Chaque ligne de fait porte une clé `source_id` vers `Dim_Source`, qui contient le libellé
  d'attribution, l'URL et la licence.
- Le rapport affiche les attributions dans une page « Sources et méthode » et dans le pied des
  visuels concernés.
- Les licences sont vérifiées pour chaque nouvelle source avant intégration ; une source dont la
  licence interdit la redistribution ne sera **pas** republiée dans le dépôt (seul le code de
  collecte le serait).
