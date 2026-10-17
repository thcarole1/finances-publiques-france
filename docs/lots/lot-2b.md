# Lot 2b — Où va l'argent ? Le Sankey

## Livré

| Élément | Détail |
|---|---|
| Table | `Pres_Flux_Sankey` (présentation, dérivée) : pays × année × lecture × étape × source × destination |
| Étape 1 | **Qui paie → qui encaisse** : prélèvements par payeur (`Fait_Prelevements_Fonction`), autres recettes (hors transferts reçus d'autres administrations), **emprunt** (déficit de chaque administration) |
| Étape 2 | **Qui encaisse → qui dépense** : ce que chaque administration garde, et ses transferts aux autres (`Fait_Transferts_APU`) |
| Étape 3 | **Qui dépense → pour quoi** : dépense **consolidée** par fonction COFOG ; un excédent éventuel forme un flux « Excédent » |
| Lectures | Chaque flux existe pour les trois lectures du payeur (légale, économique, par base) : un segment ne filtre que l'étape 1 |
| Imputation | Les éliminations par fonction sont réparties entre administrations versantes par **ajustement RAS** (`int_sankey__imputation_eliminations`, modèle Python) : les deux marges publiées sont respectées |
| Contrôle | QC-A06b (avertissement) : équilibre des nœuds à 2 % près |
| Power BI | Table, 2 relations, mesure **Flux (M€)** ; visuel **Sankey Chart** (Microsoft, AppSource) à ajouter dans Desktop (`powerbi/README.md`) |

## France 2023 (lecture économique)

- Les salariés financent la Sécurité sociale à hauteur de **493 Md€** (cotisations patronales
  comprises, en lecture économique) ; l'emprunt apporte **154 Md€** à l'État.
- L'État garde 565 Md€, transfère 58 Md€ aux collectivités et 24 Md€ à la Sécurité sociale.
- Dépense consolidée : protection sociale **658 Md€**, santé 250, affaires économiques 178,
  services généraux 175, enseignement 142…

## Limites

- **Équilibre des nœuds** : à 0,5 Md€ près pour l'État et les collectivités en France ; 4,5 Md€
  (0,6 %) pour la Sécurité sociale, car les prélèvements (`gov_10a_taxag`) et les comptes
  (`gov_10a_main`) sont mis à jour à des dates différentes.
- **Norvège** : Eurostat ne publie pas de comptes de sécurité sociale séparés ; les nœuds
  s'équilibrent mal (avertissements QC-A06b). Quelques années au Danemark aussi.
- Le Sankey n'est calculé que pour les pays-années où les trois sources existent (la dépense par
  fonction est publiée environ 9 mois après les comptes).
- L'imputation RAS est une estimation statistique : elle respecte les totaux publiés, pas le
  détail réel (non publié) des transferts par fonction.
