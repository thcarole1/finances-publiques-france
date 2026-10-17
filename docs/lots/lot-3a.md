# Lot 3a — Dette annuelle

## Livré

| Élément | Détail |
|---|---|
| Collecte | Eurostat `gov_10dd_edpt1` (dette notifiée, par sous-secteur et instrument), `gov_10dd_ggd` (par détenteur), `irt_lt_mcby_m` (taux à 10 ans, mensuel). Le collecteur retire et signale les pays absents d'un jeu (Norvège, Suisse…) |
| Faits | `Fait_Dette` (sous-secteurs + éliminations), `Fait_Dette_Instrument`, `Fait_Detention_Dette`, `Fait_Taux_Marche` |
| Dimensions | `Dim_Instrument_Dette` (obligations, titres de court terme, prêts, dépôts ; durée à l'origine), `Dim_Detenteur` (étranger, banque centrale, banques, assureurs et fonds, entreprises et ménages) |
| Contrôle | QC-B13 : même total de dette dans les trois tables |
| Mesures | Dette (M€, Md€, % du PIB, par habitant), semi-additives ; taux moyen payé ; croissance du PIB en valeur ; décomposition de la variation du ratio (déficit hors intérêts, effet boule de neige, autres facteurs) ; trois phrases |
| Rapport | Pages « 6. La dette » et « 7. À qui doit-on ? » ; Comparer et Glossaire deviennent 8 et 9 ; cinq termes ajoutés au glossaire |

## Vérifié (France)

| Indicateur | 2024 | 2025 | Référence |
|---|---|---|---|
| Dette | 3 306 Md€ | 3 460 Md€ | Eurostat (notification d'avril 2026) |
| Dette en % du PIB | 112,6 % | 115,7 % | INSEE : 113,2 % en 2024 (écart dû au millésime du PIB : on rapporte au PIB Eurostat le plus récent) |
| Dette par habitant | 48 070 € | 50 153 € | — |
| Taux moyen payé | 1,94 % | 2,02 % | intérêts 60,1 et 66,6 Md€ |
| Croissance du PIB en valeur | 3,6 % | 1,9 % | — |
| Variation du ratio | +3,1 pt | +3,1 pt | dont déficit hors intérêts +3,7 / +2,9 ; boule de neige −1,7 / +0,1 |
| Détenteurs (2024) | étranger 52,6 %, banque centrale 19,3 %, banques 16,2 %, assureurs et fonds 10,9 %, ménages et entreprises 1,0 % | | |

En 2025, le taux moyen payé dépasse pour la première fois la croissance de l'économie : l'effet
boule de neige redevient positif.

## Reporté

- Échéancier titre par titre et durée restante (AFT inaccessible ; Eurostat ne publie pas la durée restante pour la France).
- Lot 3b : dette et comptes trimestriels, détail État / organismes (`gov_10q_ggdebt`), courbe des taux BCE.
