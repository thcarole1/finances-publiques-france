# 08 — Scénarios et projections

## 1. Trois types de scénarios, une seule dimension

| Type | Exemple | Où vit-il ? | Comment se calcule-t-il ? |
|---|---|---|---|
| **Réel** | Données observées | Faits F01 à F20 | — |
| **Officiel** | Trajectoire du gouvernement (octobre 2025), prévisions de la Commission (printemps 2026), FMI WEO (avril 2026) | `Fait_Hypotheses` (tous millésimes) | Projection Python à partir des hypothèses publiées |
| **Personnel** | « Choc de taux », « Austérité 2027 », « Relance » | `scenarios/*.yml` → `Fait_Hypotheses` | Projection Python |
| **Curseurs** | Réglages en direct dans le labo | Paramètres What-if (non sauvegardés) | DAX en direct |

## 2. Simulations statiques (« et si… ? »)

Sans effet en retour sur l'économie : on modifie une recette ou une dépense, on lit l'effet
mécanique sur le solde.

| Paramètre (What-if) | Effet simulé |
|---|---|
| `Param_Delta_TVA` (points de taux normal) | Δ recettes = recettes de TVA × Δ taux ÷ taux implicite moyen × (1 − élasticité de l'assiette) |
| `Param_Delta_Depense_Fonction` (%) appliqué à la fonction sélectionnée | Δ dépenses = dépenses de la fonction × % |
| `Param_Delta_Masse_Salariale` (%) avec filtre de fonction | Δ dépenses sur `D1` uniquement (ex. éducation seulement) |
| `Param_Delta_Prestations` (%) | Δ dépenses sur `D62` |
| `Param_Elasticite_Assiette` | 0 par défaut ; permet un effet de comportement simplifié et explicite |

Ces paramètres sont des **ordres de grandeur pédagogiques** : le rapport le précise, et
renvoie vers les chiffrages officiels quand ils existent.

## 3. Projection de la dette

### Équation de base

Avec *d* la dette en % du PIB, *i* le taux apparent, *g* la croissance nominale du PIB,
*sp* le solde primaire en % du PIB et *asf* l'ajustement stock-flux en % du PIB :

```
d(t) = d(t−1) × (1 + i(t)) / (1 + g(t)) − sp(t) + asf(t)
```

### Deux moteurs, un même résultat attendu

**a) DAX en direct (curseurs).** DAX ne sait pas faire de récursion, mais la formule se déplie :

```
d(T) = d(0) × Π f(k)  −  Σ [ (sp(t) − asf(t)) × Π f(k) pour k > t ]       avec f(k) = (1 + i(k)) / (1 + g(k))
```

Ce qui s'écrit avec `PRODUCTX` et `SUMX` sur une table d'années. Avec des curseurs **constants**
sur l'horizon (*i*, *g*, *sp*), c'est simple et rapide. Le taux apparent y est un paramètre
direct : pas de modélisation fine du refinancement.

**b) Python (scénarios sauvegardés), dans `projection/`.** Calcul année par année, avec
**refinancement explicite** :

1. on part de l'échéancier AFT (F11) : quelle dette arrive à échéance chaque année ;
2. la dette arrivant à échéance + le déficit de l'année sont refinancés **au taux de marché
   supposé** du scénario, selon une structure d'émission (part court / moyen / long terme) ;
3. la charge d'intérêts de l'année = coupons des titres existants + coupons des nouvelles
   émissions + effet de l'inflation sur les titres indexés ;
4. on obtient le taux apparent, puis le solde et la dette.

C'est ce qui reproduit la lenteur de transmission des hausses de taux, liée à la durée de vie
moyenne de la dette. La dette de l'État (négociable) est traitée en détail ; le reste de la
dette publique suit une règle simplifiée (taux apparent du dernier exercice observé, puis
convergence vers le taux de marché), documentée dans le code.

**Contrôle croisé** : avec des hypothèses constantes et sans refinancement explicite, les deux
moteurs doivent donner le même résultat (test automatisé).

## 4. Format d'un scénario personnel

`scenarios/choc-de-taux-2027.yml` :

```yaml
id: PERSO_CHOC_TAUX_2027
libelle: Choc de taux en 2027
auteur: thcarole1
base: GOUV_PLF_2026          # trajectoire de départ (Dim_Scenario)
description: >
  Hausse de 150 points de base du taux à 10 ans en 2027, croissance inchangée.
horizon: 2036
hypotheses:                    # surcharges par rapport au scénario de base
  taux_10_ans:
    2027: +1.5                 # en points, relatif à la base
    2028: +1.5
  croissance_volume:
    2027: 0.8                  # en %, valeur absolue
emission:
  part_court_terme: 0.10
  maturite_moyenne_emissions: 9
```

- Une surcharge est **relative** (`+1.5`) ou **absolue** (`0.8`) ; les années non précisées
  reprennent la base.
- Le schéma est validé en CI (QC-B11). Chaque modification de scénario passe par une PR :
  l'historique Git **est** l'historique de tes scénarios.

## 5. Historique des prévisions

- `Fait_Hypotheses` conserve chaque trajectoire officielle avec sa **date de publication**.
- Mesures : erreur de prévision par institution et par **horizon** (prévision de l'année en
  cours, N+1, N+2), biais moyen (optimisme ou pessimisme systématique), erreur absolue moyenne.
- Visuel phare : le « **graphique en spaghetti** » — les trajectoires successives de dette ou de
  déficit annoncées chaque année, superposées à la réalité.
