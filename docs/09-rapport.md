# 09 — Rapport Power BI

## 1. Structure

Trois espaces, accessibles depuis une page d'accueil :

1. **Comprendre** — un parcours guidé, du simple au complexe, une question par page.
2. **Explorer** — des pages d'analyse libres, pilotées par des paramètres de champ.
3. **Simuler** — le laboratoire de scénarios.

Une **couche pédagogique** traverse les trois : info-bulles explicatives, encadrés
« Comprendre », glossaire interactif.

## 2. Parcours guidé « Comprendre »

| # | Page | Question | Visuels principaux | Lot |
|---|---|---|---|---|
| 1 | Accueil | De quoi parle-t-on ? | Chiffres clés de l'année (dépenses, recettes, solde, dette, en Md€, % du PIB et € par habitant) ; navigation | 1 |
| 2 | Combien ? | Quel poids des administrations dans l'économie ? | Dépenses et recettes en % du PIB depuis 1995, repères de crises ; « sur 1 000 € de richesse produite… » | 1 |
| 3 | Qui paie ? | D'où viennent les recettes ? | Treemap par prélèvement ; répartition par payeur avec bascule de convention d'incidence | 1 |
| 4 | Où va l'argent ? | À quoi sert la dépense ? | « Pour 1 000 € de dépense publique » par fonction ; exploration fonction → sous-fonction → nature | 1 |
| 5 | Qui fait quoi ? | Qui encaisse, qui dépense ? | **Sankey** prélèvements → administration qui encaisse → administration qui dépense → fonction ; bascule consolidé / non consolidé | 2 |
| 6 | La dette | Combien, à qui, à quel coût ? | Dette en % du PIB, charge d'intérêts, taux, détenteurs, échéancier, effet boule de neige | 3 |
| 7 | Qui reçoit ? | Qui gagne, qui perd à la redistribution ? | Par décile : prélèvements, prestations, services publics ; monétaire vs élargie côte à côte | 5 |
| 8 | Le budget en débat | Que vote le Parlement ? | Missions LOLF, branches de la Sécu, ONDAM ; voté vs exécuté | 6 |
| 9 | Ma commune | Que se passe-t-il près de chez moi ? | Fiche commune : budget par habitant, dette, taux de taxe foncière, comparaison à la strate | 7 |
| 10 | La France face aux autres | Sommes-nous une exception ? | Classements UE27 et OCDE, avertissements de comparabilité | 1 puis 8 |
| 11 | Et demain ? | Où mène la trajectoire actuelle ? | Trajectoires officielles vs réalité passée (« spaghetti »), projections de dette | 4 |

### Mise en œuvre (lot R1)

Livrées : pages 1 à 5, page 10 (« Comparer ») et un glossaire (`powerbi/README.md`). Chaque page
porte une phrase de synthèse calculée (mesures `Phrase : …`, dossier « 20 Pédagogie ») et un
encadré « Comprendre ». Les segments Pays et Année sont synchronisés entre les pages.

Lot 3a : page 6 (« La dette »), en deux pages : « La dette » (montant, décomposition de sa
variation) et « À qui doit-on ? » (détenteurs, instruments, taux). L'échéancier titre par titre
est reporté (source AFT inaccessible).

**Finition (version 1.0)** : sommaire cliquable sur l'accueil, info-bulles de définition
alimentées par le glossaire, repères des crises au survol des courbes annuelles, thème versionné
(`StaticResources/RegisteredResources/FinancesPubliques.json`, en lieu et place de
`powerbi/theme.json` prévu au § 6).

## 3. Espace « Explorer »

| Page | Contenu |
|---|---|
| Dépenses | Matrice fonction × nature × sous-secteur, axe et unité au choix (`FP_Axe_Depense`, `CG_Unite`) |
| Recettes | Prélèvement × payeur × sous-secteur bénéficiaire |
| Comparaison internationale | N'importe quel indicateur, pays au choix, unité au choix |
| Dette et taux | Séries trimestrielles, courbe des taux, *spreads*, échéancier par instantané |
| Révisions | Un chiffre à travers ses millésimes |
| Collectivités | Carte, classements, comparaisons de communes |
| Sources et méthode | Fraîcheur, contrôles qualité, licences, attributions |

## 4. Laboratoire de scénarios « Simuler »

- **Simulation statique** : curseurs TVA, dépenses par fonction, masse salariale, prestations →
  effet sur le solde (Md€ et % du PIB).
- **Projection en direct** : curseurs croissance, inflation, taux, solde primaire → trajectoire de
  dette sur 10 ans, comparée à la trajectoire officielle choisie.
- **Scénarios sauvegardés** : sélection de plusieurs scénarios (officiels et personnels), superposés
  sur un même graphique, avec tableau des écarts.
- Un encart rappelle les limites : projections mécaniques, sans effet de rétroaction.

## 5. Couche pédagogique

| Élément | Mise en œuvre |
|---|---|
| Info-bulle « définition » sur chaque indicateur | Pages d'info-bulle alimentées par `Dim_Glossaire` via `Dim_Indicateur` |
| Encadrés « Comprendre » | Bouton « ? » ouvrant un signet avec la définition longue et un exemple |
| Glossaire interactif | Page dédiée, recherche par terme, liens vers les pages où la notion apparaît |
| Repères historiques | Annotations des crises (2008-09, 2010-12, 2020-21, 2022-23) issues de `Dim_Date[periode_historique]` |
| Ordres de grandeur | Conversions parlantes : € par habitant, « sur 1 000 € », « par jour » |
| Avertissements | Comparabilité faible, valeurs provisoires, conventions différentes |

## 6. Principes de conception visuelle

- **Aucun sigle ni code technique dans un visuel** (APUL, ODAC, ASSO, codes SEC ou COFOG…) : des
  libellés en clair ; le terme technique figure seulement dans l'info-bulle ou le glossaire.
- Une question par page, le titre de la page **est** la question.
- Unité toujours visible dans le titre ou le sous-titre du visuel (le groupe de calcul `CG_Unite`
  fournit un libellé dynamique).
- Palette sobre et cohérente : une couleur par grand bloc (État, Sécurité sociale,
  collectivités) réutilisée dans tout le rapport ; couleurs accessibles (contraste, daltonisme).
- Thème Power BI versionné dans le dépôt (`powerbi/theme.json`).
