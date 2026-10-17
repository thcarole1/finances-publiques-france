# 01 — Cadrage

## 1. Objectif

Construire un modèle de données **complet et versatile** sur les finances publiques françaises,
et un rapport Power BI qui réponde, pour un contribuable, à trois questions :

1. **Qui paie ?** Quels prélèvements, versés par qui, et pesant sur quels niveaux de vie.
2. **Combien ?** En montants, en % du PIB, par habitant, dans le temps et face aux autres pays.
3. **Où va l'argent ?** Par fonction (santé, retraites, éducation…), par nature (salaires,
   prestations, investissement, intérêts…) et par administration qui dépense.

Le modèle doit aussi permettre de **tester des scénarios** : simulations statiques, projections
de dette, comparaison avec les trajectoires officielles et avec les prévisions passées.

## 2. Choix de conception validés

| # | Sujet | Choix retenu | Conséquence pour le modèle |
|---|---|---|---|
| 1 | Finalité | Conception du dashboard, fil rouge « qui paie, combien, où va l'argent » | Le flux recettes → administrations → dépenses structure le rapport |
| 2 | Périmètre | Toutes les administrations publiques (S13) | Dimension sous-secteur hiérarchique |
| 3 | Angle recettes | Par type de prélèvement + par payeur + par niveau de vie | Fait prélèvements + table de répartition par payeur + fait redistribution |
| 4 | Profil | PL-300, modèle versatile | Constellation, groupes de calcul, paramètres de champ |
| 5 | Scénarios | Exploration + simulations statiques + projections | Séparation réel / hypothèses / projections |
| 6 | Temps | Annuel depuis 1995 + trimestriel récent | Deux grains temporels, une dimension Date commune |
| 7 | International | UE27 + grands pays de l'OCDE hors UE | Dimension Pays, conversions de devises, indicateur de comparabilité |
| 8 | Collaboration | GitHub, branches + pull requests | Format PBIP/TMDL, tout est texte et versionné |
| 9 | Dépenses | COFOG (2 niveaux) × nature SEC 2010 | Fait dédié aux dépenses par fonction |
| 10 | Redistribution | Monétaire + élargie ; OpenFisca plus tard | Fait redistribution ; dimension ménage type préparée |
| 11 | Sous-secteurs | Consolidé / non consolidé avec bascule + matrice des transferts | Écritures d'élimination + fait transferts |
| 12 | Dette | Stock, intérêts, taux, détenteurs, maturité, échéancier AFT | Quatre faits dédiés à la dette et aux taux |
| 13 | Hypothèses | Curseurs + trajectoires officielles + scénarios personnels versionnés | Dimension Scénario, fichiers de scénarios dans le dépôt |
| 14 | Budgets votés | État (LOLF) et Sécurité sociale, voté et exécuté | Deux faits budgétaires, correspondance indicative vers COFOG |
| 15 | Collectivités | Détail par collectivité + fiscalité locale | Dimension géographique, table de passage des communes |
| 16 | Versions | Millésimes des données + historique des prévisions | Dimension Millésime, mesures d'erreur de prévision |
| 17 | Collecte | GitHub Actions planifié + contrôles qualité bloquants | Contrats de données et tests automatisés |
| 18 | Rapport | Parcours guidé + exploration + labo de scénarios + couche pédagogique | Glossaire en table, pages d'info-bulle |

## 3. Hors périmètre (pour l'instant)

- Simulation de ménages types avec **OpenFisca** : prévue, la dimension `Dim_Menage_Type`
  est préparée pour l'accueillir sans refonte.
- **Journal automatique des révisions** : prévu, il exploitera les millésimes déjà conservés.
- Modélisation **macroéconomique bouclée** (effets d'une hausse d'impôt sur la croissance) :
  les simulations restent statiques, avec au plus une élasticité paramétrable (voir `08`).
- **Comptes financiers complets** des administrations (actifs, dette nette) : la dette au sens
  de Maastricht est couverte ; la dette nette et le patrimoine pourront être ajoutés ensuite.
- Données **individuelles** de contribuables : aucune n'est collectée.

## 4. Principes directeurs

1. **Une seule langue comptable de référence : la comptabilité nationale (SEC 2010).**
   C'est elle qui permet de comparer les pays et les années. Les budgets votés (LOLF, LFSS) sont
   modélisés à part, et jamais additionnés avec la comptabilité nationale.
2. **Aucune mesure ne peut produire un double comptage.** La consolidation repose sur des
   écritures d'élimination explicites (voir `05`), pas sur la vigilance de l'utilisateur.
3. **Le réel, les hypothèses et les projections ne se mélangent pas.** Chaque valeur porte un
   scénario ; « Réel » est un scénario parmi d'autres.
4. **Rien n'est écrasé.** Chaque collecte produit un instantané daté (millésime).
5. **Chaque chiffre est traçable** jusqu'à sa source, son jeu de données et sa date de collecte.
6. **Les conventions sont explicites et paramétrables** : par exemple, l'attribution d'un impôt
   à un payeur est une convention documentée, pas une vérité (voir l'incidence fiscale, `04`).
7. **La pédagogie fait partie du modèle** : définitions, avertissements de comparabilité et
   explications sont des données, au même titre que les montants.

## 5. Découpage en lots

| Lot | Contenu | Pages débloquées |
|---|---|---|
| 0 | Dépôt, conventions, squelette CI, **spécification (ce document)** | — |
| 1 | Socle Eurostat/INSEE : comptes annuels, COFOG × nature, prélèvements, contexte macro | Combien ? Où va l'argent ? Qui paie (par prélèvement) ? |
| 2 | Sous-secteurs, consolidation, transferts entre administrations | Sankey complet |
| 3 | Dette, AFT, taux, comptes trimestriels | La dette |
| 4 | Hypothèses, projections, millésimes des prévisions | Et demain ? Labo de scénarios |
| 5 | Redistribution monétaire et élargie | Qui paie, qui reçoit ? |
| 6 | Budgets votés et exécutés État et Sécurité sociale | Le budget en débat |
| 7 | Collectivités et fiscalité locale | Ma commune |
| 8 | Pays de l'OCDE hors UE | La France face au monde |
| Plus tard | OpenFisca, journal des révisions | Mon ménage type |

La couche pédagogique (glossaire, info-bulles, encadrés « Comprendre ») avance avec chaque lot.
