# Lot 2a — Qui finance qui ? Transferts entre administrations

## Livré

| Élément | Détail |
|---|---|
| Source | Eurostat `gov_10a_main`, postes « dont au sous-secteur … » (`D4PAY_S131x`, `D7PAY_S131x`, `D9PAY_S131x`) : ce que chaque sous-secteur verse à chacun des autres. Déjà collecté depuis le lot 1 : **aucune nouvelle source** |
| Fait | `Fait_Transferts_APU` (F06) : pays × année × sous-secteur versant × sous-secteur receveur × opération (revenus de la propriété, transferts courants dont dotations, transferts en capital dont aides à l'investissement) |
| Dimension | `Dim_Sous_Secteur_Receveur` : rôle « receveur » de `Dim_Sous_Secteur` (relations simples et actives) |
| Contrôle | QC-A05 : les transferts expliquent les éliminations de la consolidation (`S13_ELIM`) à 5 % près — aucun écart sur les 31 pays |
| Power BI | 2 tables, 7 relations, mesure **Transferts entre administrations (M€)** |

## France 2023

| Versant → receveur | Md€ |
|---|---|
| État et organismes centraux → collectivités locales | 58,0 |
| État et organismes centraux → Sécurité sociale | 24,0 |
| Sécurité sociale → État et organismes centraux | 10,2 |
| Sécurité sociale → collectivités locales | 8,5 |
| Collectivités locales → État et organismes centraux | 7,1 |
| Collectivités locales → Sécurité sociale | 1,4 |
| **Total** (= éliminations de la consolidation) | **≈ 109** |

🎓 **À savoir pour lire le Sankey.** Les fractions d'impôts affectées (TVA versée à la Sécurité
sociale ou aux collectivités, par exemple) **ne sont pas des transferts** en comptabilité nationale :
elles sont enregistrées directement comme recettes fiscales de l'administration bénéficiaire
(`Fait_Prelevements`, par sous-secteur). Elles apparaissent donc dans l'étape « qui encaisse ».

## Reporté au lot 2b

Détail INSEE (État / organismes divers, régimes de sécurité sociale), explication de l'écart sur
les prélèvements obligatoires (Eurostat 43,2 % / INSEE 42,8 % en 2024), table `Pres_Flux_Sankey`
et Sankey dans le rapport. Voir `docs/REPRISE.md`.
