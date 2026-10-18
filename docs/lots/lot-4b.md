# Lot 4b — Scénarios sauvegardés

## Livré

| Élément | Détail |
|---|---|
| Moteur | `projection/moteur.py` : projection annuelle avec refinancement (stock de départ amorti sur sa durée de vie moyenne, échéances et besoin de financement empruntés au taux du scénario, part à court terme) ; cibles de solde public possibles (trajectoires officielles) |
| Scénarios | `TENDANCIEL` (tous pays), `GOUV_PLF_2027` (France), scénarios personnels `scenarios/*.yml` (deux exemples : choc de taux, effort progressif) ; schéma enrichi (`pays`, `solde_public`, `taux_court`, `duree_vie_stock`) |
| Gouvernement | `ref_previsions_gouvernement.csv` : rapport d'avancement d'avril 2026 et projet de loi de finances pour 2027, document cité pour chaque chiffre ; ces éditions apparaissent aussi dans le graphique en spaghetti (en rouge) |
| Modèle | `Fait_Projections` (dbt, modèle Python), `Dim_Scenario`, mesures du dossier « 32 Scénarios » |
| Rapport | Page « 13. Mes scénarios » ; Prévisions, Qui se trompe ? et Glossaire deviennent 14, 15 et 16 |
| Tests | `tests/test_projection.py` : contrôle croisé avec la formule du laboratoire, transmission lente d'une hausse des taux, cibles du gouvernement atteintes, identités comptables |

## Résultats (France, départ 2025 : dette 115,7 %)

| Scénario | 2027 | 2030 | 2035 | Taux moyen payé en 2035 |
|---|---|---|---|---|
| Tendanciel | 119,9 % | 127,8 % | 144,6 % | 3,4 % |
| Gouvernement (PLF 2027) | 120,2 % | 126,8 % | 141,4 % | 3,4 % |
| Exemple : choc de taux 2027 | 120,5 % | 128,5 % | 144,9 % | 3,5 % |
| Exemple : effort de 0,5 point par an | 119,4 % | 122,7 % | 129,4 % | 3,4 % |

Le gouvernement annonce 119,3 % en 2026 et 121,7 % en 2027 ; le moteur donne 118,5 % et 120,2 % :
l'écart vient des opérations de trésorerie (ajustement stock-flux), non modélisées, et du PIB.

## Limites

- Amortissement uniforme de la dette de départ (pas d'échéancier titre par titre).
- Pas d'effet de l'inflation sur la dette indexée, pas d'effet en retour sur la croissance.
- Trajectoires du gouvernement : seules deux éditions saisies ; au-delà des années publiées, le
  solde hors intérêts est maintenu (le gouvernement vise un déficit sous 3 % en 2029 sans
  trajectoire chiffrée dans le rapport d'avancement 2026).
