# 07 — Qualité des données

## 1. Principe

Chaque collecte passe par trois niveaux de contrôle. Un contrôle **bloquant** (B) en échec
arrête le pipeline : aucune donnée n'est publiée, une *issue* d'alerte est ouverte avec le
détail. Un **avertissement** (A) laisse passer la collecte mais figure dans la PR de données.

| Niveau | Question | Exemples |
|---|---|---|
| 1. Technique | Le fichier est-il lisible et conforme à son contrat ? | Schéma, types, clés, doublons |
| 2. Comptable | Les identités de la comptabilité nationale sont-elles respectées ? | Recettes − dépenses = solde |
| 3. Cohérence | Les chiffres sont-ils plausibles et cohérents entre sources et dans le temps ? | INSEE ≈ Eurostat, ruptures |

## 2. Contrôles bloquants

| Code | Contrôle | Table(s) | Tolérance |
|---|---|---|---|
| QC-B01 | **Contrat de schéma** : colonnes, types, nullabilité conformes au contrat du modèle dbt | Toutes | 0 |
| QC-B02 | **Unicité du grain** : aucune ligne en double sur les clés du grain | Toutes | 0 |
| QC-B03 | **Exhaustivité des feuilles** : Σ feuilles de dépense = dépenses totales publiées (OTE) ; idem recettes (TR) | F01 | 0,05 % ou 1 M€ |
| QC-B04 | **COFOG = total** : Σ fonctions = dépenses totales de F01 (pays, année, sous-secteur) | F02 × F01 | 0,1 % |
| QC-B05 | **Consolidation** : Σ sous-secteurs + `S13_ELIM` = S13 publié | F01, F09 | 0,05 % |
| QC-B06 | **Dette annuelle** : dette au T4 = dette annuelle notifiée | F09 | 0,1 % |
| QC-B07 | **Échéancier AFT** : Σ encours par titre = encours total publié | F11 | 0,01 % |
| QC-B08 | **Intégrité référentielle** : toute clé étrangère existe dans sa dimension (sinon `_NA` explicite, compté) | Toutes | 0 clé orpheline |
| QC-B09 | **Pont payeur** : Σ coefficients = 1 par prélèvement et par convention | `Map_Prelevement_Payeur` | 0,001 |
| QC-B10 | **Identité du solde** : recettes − dépenses = besoin/capacité de financement publié (B9) | F01 | 0,05 % ou 1 M€ |
| QC-B11 | **Scénarios valides** : chaque fichier `scenarios/*.yml` respecte le schéma, variables et années connues | F13 | 0 |
| QC-B12 | **Unités** : ordre de grandeur cohérent (ex. dépenses France entre 40 et 70 % du PIB) — détecte une erreur d'échelle millions/milliards | F01, F04 | Bornes par pays |

## 3. Avertissements

| Code | Contrôle | Seuil par défaut |
|---|---|---|
| QC-A01 | **Complétude** : pays × années attendus présents | Toute absence nouvelle |
| QC-A02 | **Rupture** : variation annuelle d'une série au-delà de son historique | > 4 écarts-types |
| QC-A03 | **Révision** : écart entre le nouveau millésime et le précédent sur une même année | > 0,3 pt de PIB ou > 1 % |
| QC-A04 | **Cohérence INSEE / Eurostat** (France, même agrégat, millésimes proches) | > 0,2 % |
| QC-A05 | **Transferts** : matrice F06 cohérente avec les éliminations de F01 | > 2 % |
| QC-A06 | **Fraîcheur** : une source n'a pas été mise à jour depuis plus longtemps que prévu | > 1,5 × la fréquence |
| QC-A07 | **Trimestriel vs annuel** : Σ trimestres bruts = année | > 0,5 % |
| QC-A08 | **Collectivités** : collectivités disparues ou apparues sans fusion connue dans `Map_COG_Passage` | Toute occurrence |
| QC-A09 | **Valeurs provisoires** : part des valeurs marquées provisoires ou estimées | Signalement |

## 4. Mise en œuvre

- Contrôles techniques : contrats de modèles dbt + tests dbt génériques (`unique`, `not_null`,
  `relationships`, `accepted_values`).
- Contrôles comptables et de cohérence : tests dbt *singuliers* (requêtes SQL qui renvoient les
  lignes en anomalie ; zéro ligne = succès).
- Chaque exécution produit `qualite/rapport_<date>.md` (résumé lisible) et
  `qualite/resultats_<date>.json` (détail), joints à la PR de données.
- Les tolérances sont centralisées dans `contracts/tolerances.yml` et modifiables par PR.

## 5. Qualité visible dans le rapport

- Les valeurs **provisoires** ou **estimées** sont signalées (marqueur et info-bulle).
- Une page **« Sources et méthode »** affiche, par source : dernier millésime, date de collecte,
  résultats des derniers contrôles, licence et attribution.
- Les comparaisons à faible comparabilité (pays hors UE, budgets votés vs comptabilité
  nationale) affichent un avertissement explicite.
