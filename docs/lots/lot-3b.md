# Lot 3b — Dette trimestrielle et taux d'intérêt

## Livré

| Élément | Détail |
|---|---|
| Collecte | Eurostat `gov_10q_ggdebt`, `gov_10q_ggnfa`, `namq_10_gdp` ; **nouveau connecteur INSEE** (BDM, SDMX public) : `DETTE-TRIM-APU-2020`, `DETTE-NEGOCIABLE-ETAT` ; **nouveau connecteur BCE** : courbe des taux (flux YC) |
| Faits | `Fait_Dette_Trimestrielle`, `Fait_Macro_Trimestriel`, `Fait_Comptes_APU_Trimestriels`, `Fait_Dette_Contributions` (France), `Fait_Dette_Negociable_Etat` (France), `Fait_Courbe_Taux` |
| Dimensions | `Dim_Agregat_Trimestriel`, `Dim_Composante_Dette_Etat` ; `Dim_Sous_Secteur` gagne « État » et « Agences de l'État » (niveau 2) |
| Contrôles | QC-B14, QC-B15 (avertissement), QC-A08 (avertissement) ; QC-B06 en avertissement |
| Mesures | Dette trimestrielle (Md€, % du PIB sur quatre trimestres), dernier trimestre connu (INSEE pour la France), hausse sur un an, solde trimestriel CVS, écart de taux avec l'Allemagne, courbe des taux, parts indexée et à court terme de la dette de l'État, deux phrases |
| Rapport | Pages « 8. Les derniers trimestres » et « 9. Les taux d'intérêt » ; Comparer et Glossaire deviennent 10 et 11 ; quatre termes ajoutés au glossaire |

## Vérifié (France)

| Indicateur | Valeur | Référence |
|---|---|---|
| Dette au 2e trimestre 2026 (INSEE) | 3 596 Md€, 119,1 % du PIB sur un an | INSEE : 119,0 % |
| Hausse sur un an | +178 Md€ (environ 490 M€ par jour) | 3 417 Md€ au 2e trimestre 2025 |
| Répartition (2e trimestre 2026) | État 2 942, agences 69, collectivités 275, Sécurité sociale 309 Md€ | Σ = total INSEE |
| Taux à 10 ans 2025 | France 3,37 %, Allemagne 2,61 % (écart 0,76 point) | Eurostat |
| Dette de l'État indexée sur l'inflation (fin 2025) | 11,2 % ; à court terme 7,2 % | INSEE d'après l'AFT |
| Solde du 1er trimestre 2026 (CVS) | −5,1 % du PIB | Eurostat |

## Points d'attention

- Le mois en cours de la courbe des taux est daté de la fin du mois mais porte la dernière valeur
  connue (par exemple le 16 octobre 2026).
- La dette négociable de l'État présente un écart ponctuel dans la source en octobre 2017 (QC-B15).

## Reporté

- Comptes trimestriels par sous-secteur et par nature (seul l'ensemble des administrations est repris).
- Échéancier titre par titre (AFT).
