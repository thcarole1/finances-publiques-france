# Lot 1 — Socle Eurostat

## Livré

| Élément | Détail |
|---|---|
| Connecteur | `ingestion/sources/eurostat.py` : API SDMX 2.1, SDMX-CSV compressé, **une requête par pays** (au-delà d'un certain volume, Eurostat bascule en extraction asynchrone) |
| Jeux | `gov_10a_main`, `gov_10a_exp`, `gov_10a_taxag`, `nama_10_gdp`, `nama_10_pe` |
| Couverture | UE27 + agrégats UE27 et zone euro (21 pays) + Norvège et Suisse (publiées par Eurostat), 1995 → dernière année publiée |
| Archivage brut | Release `raw-AAAA-MM-JJ`, une archive par jeu (`scripts/donnees_brutes.py`), publiée par le workflow `collecte` |
| Tables | `Dim_Pays`, `Dim_Transaction`, `Dim_COFOG`, `Dim_Prelevement`, `Dim_Source`, `Dim_Millesime`, `Dim_Indicateur` ; faits F01 à F05 |
| Contrôles | QC-B01 à B05, B08, B10, B12 (bloquants) ; QC-A01, A03, A04 (avertissements) |
| Power BI | 17 tables, relations, 18 mesures, groupes de calcul `CG_Unite` et `CG_Consolidation`, hiérarchie des fonctions ; modèle validé en CI par la bibliothèque TOM de Microsoft |

## Vérification contre les publications officielles

Comparaison avec l'INSEE, *Informations rapides* n° 78 du 27 mars 2026 (comptes 2025, premiers résultats) :

| Indicateur (France) | INSEE | Modèle (Eurostat, juillet 2026) |
|---|---|---|
| Déficit public 2024 | 5,8 % du PIB | 5,8 % |
| Déficit public 2025 | 5,1 % du PIB | 5,1 % |
| Dépenses publiques 2024 | 57,0 % du PIB | 57,0 % |
| Dépenses publiques 2025 | 57,2 % du PIB | 57,3 % |
| Recettes publiques 2025 | 52,1 % du PIB | 52,2 % |
| Charge d'intérêts 2025 | 2,2 % du PIB | 2,2 % |
| Prélèvements obligatoires 2024 | 42,8 % du PIB | 43,2 % (définition Eurostat) |

Les écarts de 0,1 point viennent des révisions de mai 2026, intégrées par Eurostat en juillet.

**Écart sur les prélèvements obligatoires.** La définition Eurostat retenue (impôts + cotisations
sociales effectives − montants non recouvrables) dépasse de 0,4 point la définition française de
l'INSEE. L'écart sera documenté précisément, et la série INSEE ajoutée, avec la source INSEE (lot 2).

## Choix de modélisation propres au lot

- **Codes de nature** : les feuilles portent des codes explicites suffixés par le sens
  (`D41_PAY` pour les intérêts versés, `D4_REC` pour les revenus de la propriété reçus), car un même
  code SEC existe en dépense et en recette.
- **Deux jeux de feuilles de nature** : `Fait_Comptes_APU_Annuels` isole les intérêts (`D41_PAY`) ;
  `Fait_Depenses_Fonction` ne connaît que les revenus de la propriété dans leur ensemble (`D4_PAY`),
  seul détail publié par fonction. L'attribut `ensemble_feuilles` de `Dim_Transaction` l'indique.
- **Nature non ventilée** (`NV_PAY`) : pour les années anciennes de certains pays, seule la dépense
  totale par fonction est publiée ; le résidu garantit Σ = total.
- **Lignes `_NA` de sous-secteur** : quand un pays-année ne publie pas ses trois sous-secteurs
  (Norvège, Malte, certaines années anciennes), l'écart avec le total n'est pas présenté comme
  une élimination mais comme « non renseigné ».
- **QC-B04** compare la somme des fonctions au total du **même jeu** (exactitude de construction) ;
  la cohérence avec `gov_10a_main`, mis à jour à une autre date, est un avertissement (QC-A04).

## Reporté

- **Répartition par payeur** (`Map_Prelevement_Payeur`, conventions légale et économique) : les
  coefficients doivent être sourcés un à un ; c'est un sous-lot dédié, avant le Sankey du lot 2.
- Source INSEE (détail État / ODAC, prélèvements obligatoires au sens français) : lot 2.
- Pays de l'OCDE hors Europe : lot 8 (la Norvège et la Suisse sont déjà couvertes via Eurostat).
