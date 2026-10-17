# 06 — Mesures et calculs

Les extraits DAX ci-dessous fixent l'**intention** et les **règles**. Les mesures réellement
implémentées sont dans `powerbi/…/tables/_Mesures.tmdl` (lot 1 : voir `docs/lots/lot-1.md`). Elles sont finalisées et
testés dans Power BI Desktop à chaque lot.

## 1. Organisation des mesures

- Toutes les mesures vivent dans une table vide `_Mesures`, rangées en **dossiers d'affichage** :
  `01 Recettes`, `02 Dépenses`, `03 Solde`, `04 Dette`, `05 Taux`, `06 Redistribution`,
  `07 Budgets votés`, `08 Collectivités`, `09 Scénarios`, `10 Contexte`, `99 Technique`.
- Une mesure de **base** par table de faits, qui ne fait qu'une somme. Toutes les autres
  mesures s'appuient sur elles, jamais directement sur les colonnes.
- Chaque mesure a une **description** (visible au survol dans le volet des champs), reprise du
  glossaire quand c'est une notion économique.
- Les mesures qui n'ont pas de sens à un grain donné renvoient `BLANK()` plutôt qu'un chiffre
  faux (ex. une dette « additionnée » sur plusieurs dates).

## 2. Mesures de base

```dax
Montant APU (M€)        = SUM ( Fait_Comptes_APU_Annuels[valeur_meur] )
Dépense fonction (M€)   = SUM ( Fait_Depenses_Fonction[valeur_meur] )
Prélèvements (M€)       = SUM ( Fait_Prelevements[valeur_meur] )
PIB (M€)                = SUM ( Fait_Macro_Annuel[pib_meur] )
Population              = SUM ( Fait_Macro_Annuel[population] )
```

## 3. Agrégats budgétaires

```dax
Dépenses publiques (M€) =
CALCULATE ( [Montant APU (M€)], Dim_Transaction[sens] = "Dépense" )

Recettes publiques (M€) =
CALCULATE ( [Montant APU (M€)], Dim_Transaction[sens] = "Recette" )

Solde public (M€) = [Recettes publiques (M€)] - [Dépenses publiques (M€)]

Charge d'intérêts (M€) =
CALCULATE ( [Montant APU (M€)], Dim_Transaction[Code nature] = "D41_PAY" )

-- Solde primaire : le solde hors charge d'intérêts.
-- C'est lui qui dit si l'État « vit au-dessus de ses moyens » hors coût du passé.
Solde primaire (M€) = [Solde public (M€)] + [Charge d'intérêts (M€)]

Taux de prélèvements obligatoires =
DIVIDE (
    CALCULATE ( [Prélèvements (M€)], Dim_Prelevement[est_prelevement_obligatoire] = TRUE () ),
    [PIB (M€)]
)
```

## 4. Qui paie ? Répartition par payeur

La répartition par payeur passe par le pont pondéré `Map_Prelevement_Payeur`, selon la
convention d'incidence choisie (légale par défaut).

```dax
Prélèvements par payeur (M€) =
VAR _convention =
    SELECTEDVALUE ( Dim_Convention_Incidence[convention_id], "LEGALE" )
VAR _repartition =
    CALCULATETABLE (
        Map_Prelevement_Payeur,
        Map_Prelevement_Payeur[convention_id] = _convention
    )
RETURN
    SUMX (
        _repartition,
        Map_Prelevement_Payeur[coefficient]
            * CALCULATE (
                [Prélèvements (M€)],
                TREATAS ( { Map_Prelevement_Payeur[prelevement_code] }, Dim_Prelevement[prelevement_code] )
            )
    )
```

`Dim_Convention_Incidence` est une table **déconnectée** (segment) ; `Dim_Payeur` et
`Dim_Prelevement` filtrent `Map_Prelevement_Payeur` par des relations simples.

## 5. Dette (mesures semi-additives)

```dax
-- Dernière date disponible dans le contexte (par pays, sous-secteur, etc.)
Dette (M€) =
VAR _derniereDate = CALCULATE ( MAX ( Fait_Dette[date_id] ) )
RETURN
    CALCULATE ( SUM ( Fait_Dette[encours_meur] ), Dim_Date[date_id] = _derniereDate )

-- Dénominateur : PIB des 4 trimestres se terminant à la date de la dette
-- (convention Eurostat pour la dette trimestrielle).
Dette (% PIB) =
VAR _derniereDate = CALCULATE ( MAX ( Fait_Dette[date_id] ) )
VAR _date =
    LOOKUPVALUE ( Dim_Date[date], Dim_Date[date_id], _derniereDate )
VAR _pib4T =
    CALCULATE (
        SUM ( Fait_Macro_Trimestriel[pib_meur] ),
        DATESINPERIOD ( Dim_Date[date], _date, -12, MONTH )
    )
RETURN DIVIDE ( [Dette (M€)], _pib4T )
```

Indicateurs dérivés :

| Mesure | Définition | Pédagogie |
|---|---|---|
| Taux apparent de la dette | Charge d'intérêts N ÷ dette fin N−1 | Le taux moyen réellement payé sur tout le stock |
| Croissance nominale du PIB | PIB N ÷ PIB N−1 − 1 | Croissance réelle + inflation |
| Écart r − g | Taux apparent − croissance nominale | Signe positif = la dette grossit d'elle-même |
| Effet boule de neige (pts de PIB) | dette/PIB N−1 × (r − g) ÷ (1 + g) | Hausse « automatique » du ratio |
| Ajustement stock-flux (M€) | Δ dette − besoin de financement | Ce qui fait varier la dette hors déficit (trésorerie, privatisations…) |
| Solde stabilisant la dette (% PIB) | − dette/PIB × (r − g) ÷ (1 + g) | Le solde primaire qu'il faudrait pour stabiliser le ratio |
| Part détenue par les non-résidents | Dette détenue par les non-résidents ÷ dette | |
| Durée de vie moyenne (années) | Σ (encours × durée restante) ÷ Σ encours, à l'instantané choisi | Vitesse de transmission d'une hausse des taux |
| Écart de taux avec l'Allemagne | Taux 10 ans pays − taux 10 ans Allemagne | Prime de risque perçue par les marchés |

**Échéancier** : l'instantané AFT se choisit avec un segment sur une table déconnectée
`Param_Instantane_AFT` ; les remboursements par année utilisent
`USERELATIONSHIP ( Fait_Dette_Titres[date_echeance_id], Dim_Date[date_id] )` et filtrent
l'instantané directement sur `Fait_Dette_Titres[date_id]`.

## 6. Groupes de calcul

### `CG_Unite` — exprimer n'importe quel montant dans l'unité choisie

| Élément | Expression (intention) | Format |
|---|---|---|
| Milliards € | `SELECTEDMEASURE () / 1000` | `#,0.0 "Md€"` |
| % du PIB | `DIVIDE ( SELECTEDMEASURE (), [PIB de référence (M€)] )` | `0.0 %` |
| € par habitant | `DIVIDE ( SELECTEDMEASURE () * 1e6, [Population de référence] )` | `#,0 "€"` |
| SPA par habitant | conversion via `ppa_eur` puis ÷ population | `#,0 "SPA"` |
| Indice base 100 | valeur ÷ valeur de l'année de base (`Param_Annee_Base`) × 100 | `0.0` |

`[PIB de référence]` et `[Population de référence]` choisissent le bon dénominateur selon que la
mesure courante est un **flux** (somme des années du contexte) ou un **stock** (année de la
dernière date), en testant `ISSELECTEDMEASURE`. Les mesures déjà exprimées en ratio sont exclues
du groupe de calcul (elles renvoient `SELECTEDMEASURE ()` inchangée).

### `CG_Temps` — variations et lissages

Valeur · Variation annuelle (absolue) · Variation annuelle (%) · Moyenne mobile 5 ans ·
Cumul depuis l'année de base · Écart à la moyenne UE27.

**Composition attendue** : l'unité s'applique **avant** la variation. Une variation de la dette
« en % du PIB » est une variation **en points** de PIB, pas un pourcentage de variation des
montants. Les précédences des deux groupes seront fixées et testées en conséquence.

### `CG_Consolidation` — la bascule demandée

| Élément | Expression |
|---|---|
| Consolidé | `SELECTEDMEASURE ()` |
| Non consolidé | `CALCULATE ( SELECTEDMEASURE (), Dim_Sous_Secteur[est_elimination] = FALSE () )` |

### `CG_Comparaison` — réel, millésimes et scénarios

Valeur · Écart au scénario de référence · Écart en % · Erreur de prévision (réalisé − prévu).
Le scénario de référence se choisit via une copie déconnectée de `Dim_Scenario`.

## 7. Paramètres de champ

| Paramètre | Contenu | Usage |
|---|---|---|
| `FP_Axe_Depense` | Fonction N1, fonction N2, nature, sous-secteur | Changer l'axe d'un même visuel |
| `FP_Axe_Recette` | Prélèvement, catégorie pédagogique, payeur, sous-secteur bénéficiaire | Idem pour les recettes |
| `FP_Indicateur` | Dépenses, recettes, solde, solde primaire, dette, intérêts, PO | Visuels « tout-en-un » |
| `FP_Comparaison_Pays` | France seule, grands voisins, UE27, OCDE | Préréglages de pays |

## 8. Scénarios et prévisions

```dax
-- Valeur d'une variable d'hypothèse pour le scénario sélectionné
Hypothèse =
CALCULATE (
    AVERAGE ( Fait_Hypotheses[valeur] ),
    Dim_Millesime[est_dernier] = TRUE ()   -- sauf analyse explicite des millésimes
)

-- Erreur de prévision : réalisé (dernier millésime) − prévu (millésime sélectionné)
Erreur de prévision du solde (pts PIB) =
    [Solde public (% PIB) réalisé] - [Solde public (% PIB) prévu]
```

Les mesures de projection en direct (curseurs) sont décrites dans `08`.

## 9. Budgets votés

| Mesure | Règle |
|---|---|
| Crédits LFI (CP) | `stade = LFI`, `type_credit = CP` imposés |
| Crédits exécutés (CP) | `stade = Exécution`, `type_credit = CP` |
| Taux d'exécution | exécutés ÷ LFI |
| Écart voté-exécuté | exécutés − LFI |
| Dépense ONDAM réalisée vs objectif | `Fait_Budget_Secu`, sous-objectifs ONDAM |
| Solde par branche | produits − charges, à stade fixé |

Une mesure de budget voté ne s'affiche **jamais** à côté d'une mesure de comptabilité nationale
sans l'avertissement « conventions différentes » (info-bulle dédiée).

## 10. Collectivités

| Mesure | Règle |
|---|---|
| Montant local (€) | Somme de `Fait_Comptes_Locaux` |
| Montant local par habitant | ÷ population de l'année (`Fait_Population_Locale`) |
| Taux moyen pondéré | Σ produits ÷ Σ bases |
| Écart à la strate | valeur commune − médiane des communes de la même strate de population |
| Rang dans la strate | `RANKX` sur les communes de la même strate |
