# Lot 1b — Qui paie ?

## Livré

| Élément | Détail |
|---|---|
| Source | Commission européenne, DG TAXUD : **listes nationales des impôts** (*National Tax Lists*, édition 2026) — chaque impôt national, son code SEC et sa **base économique** |
| Connecteur | `ingestion/sources/taxud.py` (l'URL change à chaque édition : elle est lue sur la page *Data on Taxation Trends*) |
| Répartition | `int_prelevements__parts_fonction` : part de chaque base dans chaque prélèvement, par pays et par année ; impôt sur le revenu, CSG et CRDS ventilés avec la répartition déclarée par chaque pays (*PIT split*) |
| Fait | `Fait_Prelevements_Fonction` (F03b) : `Fait_Prelevements` × parts ; **Σ des bases = F03 ligne à ligne** (contrôle QC-B09) |
| Dimension | `Dim_Fonction_Economique` : base, payeur en **lecture légale** (qui verse) et **lecture économique** (qui supporte), avec explications |
| Power BI | 3 tables, 7 relations, 2 mesures, paramètre de champ `FP_Lecture_Payeur` (légal / économique / base) |

## Bases économiques (méthodologie *Taxation Trends*)

| Code | Base | Payeur légal | Payeur économique |
|---|---|---|---|
| C | Consommation | Entreprises (redevables) | Ménages : consommateurs |
| LEYRS | Travail, part employeurs | Employeurs | Ménages : salariés (hypothèse OCDE, *Taxing Wages*) |
| LEES | Travail, part salariés | Ménages : salariés | idem |
| LNON | Revenus de remplacement | Ménages : retraités et chômeurs | idem |
| KISE | Revenus des indépendants | Ménages : indépendants | idem |
| KIH | Revenus du capital des ménages | Ménages : épargnants et propriétaires | idem |
| KIC | Bénéfices des sociétés | Sociétés | Sociétés et actionnaires (non réattribué) |
| KS | Patrimoine | Propriétaires (ménages et entreprises) | idem |
| NV | Non ventilé | — | — |

## Vérification

France 2023, comparée aux fiches pays de la Commission (*Part 2 country profiles*, avril 2026) :

| Base | Modèle | Commission |
|---|---|---|
| Consommation | 10,7 % du PIB | 10,8 % |
| Travail (y c. revenus de remplacement) | 22,6 % | 22,5 % |
| Bénéfices des sociétés | 3,0 % | 3,0 % |
| Revenus du capital des ménages | 1,9 % | 1,9 % |
| Revenus des indépendants | 1,7 % | 1,7 % |
| Patrimoine | 3,9 % | 4,0 % |

Lecture « qui paie ? » pour la France en 2023, sur les prélèvements obligatoires : les entreprises
**versent** 727 Md€ et les ménages 401 Md€ ; en lecture économique, les ménages **supportent**
1 044 Md€ et les sociétés 84 Md€ (le patrimoine, 110 Md€, n'étant pas réparti).

## Origine de chaque répartition (`type_part`)

| Type | Signification | Poids (2023, pays) |
|---|---|---|
| `NTL` | Liste nationale du pays pour l'année | ≈ 87 % |
| `PROLONGEE` | Liste nationale, année la plus proche (années non encore couvertes) | — |
| `MOYENNE_UE` | Pas de base publiée pour ce prélèvement dans ce pays : composition moyenne européenne pour le même prélèvement (Suisse, quelques prélèvements en Italie, aux Pays-Bas, en Pologne…) | ≈ 11 % |
| `AGREGAT` | UE27 et zone euro : composition des pays membres | — |
| `DEFAUT` | Cotisations imputées (D612), absentes des listes : travail, part employeurs | ≈ 2 % |
| `NV` | Montants non recouvrables (D995), sans base | < 0,1 % |

## Limites

- Les parts sont nationales (administrations publiques + institutions de l'UE) ; elles sont appliquées
  telles quelles à chaque sous-secteur. Le total S13 est exact ; la ventilation par sous-secteur est
  une approximation (ex. la CSG, versée à la Sécurité sociale, et l'impôt sur le revenu, versé à
  l'État, partagent la même feuille SEC `D51A`).
- La lecture économique repose sur des **hypothèses** usuelles, expliquées dans le modèle ; l'incidence
  réelle des cotisations patronales et de l'impôt sur les sociétés fait débat.
- Les listes nationales s'arrêtent à 2023 ou 2024 selon les pays ; les années suivantes reprennent
  la dernière composition publiée (`PROLONGEE`).
