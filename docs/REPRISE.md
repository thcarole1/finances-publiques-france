# Note de reprise

À lire en premier par toute nouvelle session de travail sur ce dépôt.
Dernière mise à jour : 17/10/2026, après le lot 2a.

## 1. Où en est le projet

| Lot | Contenu | État |
|---|---|---|
| 0 | Spécification (`docs/`), outillage, CI, projet Power BI | ✅ fusionné |
| 1 | Socle Eurostat : comptes APU, COFOG × nature, prélèvements, macro, révisions | ✅ fusionné (PR #5) |
| 1b | Qui paie ? Bases économiques (DG TAXUD), lectures légale / économique | ✅ fusionné (PR #6) |
| 2a | Transferts entre administrations (`Fait_Transferts_APU`) | PR ouverte (branche `feat/lot-2a-transferts`) |
| 2b | INSEE (détail État/ODAC, PO au sens INSEE), table et page Sankey | **à faire** |
| 3 → 8 | Dette, scénarios, redistribution, budgets votés, collectivités, OCDE | à faire (`docs/01-cadrage.md`, § 5) |

Les notes de chaque lot (livré, vérifié, reporté) sont dans `docs/lots/`.

## 2. Comment on travaille

- **Une branche et une PR par lot** ; la protection de `main` impose la PR et le job CI `controles`.
  La PR est créée par l'API REST (`gh api repos/…/pulls`) : GraphQL est bloqué dans les sessions Claude.
- **Le propriétaire fusionne** (« Squash and merge ») après avoir testé dans Power BI Desktop.
- **Les données préparées (`data/curated`) sont produites par GitHub Actions**, pas commitées depuis
  la session : déclencher `collecte.yml` sur la branche
  (`gh api -X POST repos/thcarole1/finances-publiques-france/actions/workflows/collecte.yml/dispatches -f ref=<branche>`).
  Le workflow collecte, contrôle, archive les données brutes en Release et commite `data/curated`
  sur la branche. Les commits du bot ne relancent pas la CI : ouvrir la PR **après** la collecte.
- **Les Releases** ne peuvent être créées que par GitHub Actions (refusé depuis une session Claude).
- Construction locale : `./scripts/construire.sh` (récupère les données brutes publiées si absentes).
  DuckDB est en mono-fil (`transform/profiles.yml`) : les Parquet sont identiques à l'octet entre
  local et CI. Mettre de côté (pas supprimer) les Parquet locaux avant de récupérer le commit du bot.
- **Préférence du propriétaire** : avant toute commande destructive (suppression, purge, réécriture
  d'historique), auditer l'existant, avertir explicitement des risques et proposer une sauvegarde.
- **Style d'échange** : questions séquentielles avec options A, B, C… + « Autre », une recommandation
  signalée ; pédagogie économique (🎓) ; consignes Power BI clic par clic.

## 3. Pièges connus (Power BI / TMDL)

| Piège | Règle |
|---|---|
| Apostrophe dans un nom | La doubler : `'Est fin d''année'` (test `tests/test_tmdl.py`) |
| Éléments de groupe de calcul | `ordinal` **avant** `formatStringDefinition` |
| Paramètres de champ | La définition écrite à la main est refusée par TOM : les créer dans Desktop (`powerbi/README.md`) puis récupérer le TMDL généré comme modèle |
| Tri d'une colonne | Le libellé trié doit avoir une seule valeur de tri (tests `unicite_grain` sur les référentiels) |
| Validation | Job CI `modele-powerbi` (bibliothèque TOM) ; message d'erreur lisible dans les **annotations** du check (`gh api …/check-runs/<id>/annotations`) — les journaux bruts ne sont pas accessibles depuis la session |
| Paramètres Power Query | Créés en requête vide : décocher « Activer le chargement » |

## 4. Accès réseau

Domaines autorisés côté session : Eurostat (`ec.europa.eu`), INSEE (`www.insee.fr`, `bdm.insee.fr`),
OCDE, BCE, OFGL, DG TAXUD (`taxation-customs.ec.europa.eu`, `webgate.ec.europa.eu`).
Bloqués constatés : `api.insee.fr`, `www.data.gouv.fr`, `www.aft.gouv.fr` (403). GitHub Actions a
un accès Internet complet : en dernier recours, y faire tourner l'exploration.

## 5. Prochaine étape : lot 2b

1. **INSEE** : la BDM (SDMX, `bdm.insee.fr/series/sdmx`) expose `CNA-2020-CSI` (comptes des secteurs
   institutionnels, base 2020). Y chercher le détail État (S13111) / ODAC (S13112) et l'utiliser pour
   le niveau 2 de `Dim_Sous_Secteur` ; récupérer le taux de prélèvements obligatoires INSEE et
   documenter l'écart avec la définition Eurostat (`docs/lots/lot-1.md`).
2. **`Pres_Flux_Sankey`** (dbt) : nœuds et flux *base économique (payeur) → sous-secteur qui encaisse
   → (transferts) → sous-secteur qui dépense → fonction COFOG*, par pays et année, à partir de
   `Fait_Prelevements_Fonction`, `Fait_Transferts_APU` et `Fait_Depenses_Fonction`.
   Les recettes non fiscales et le déficit (solde) doivent apparaître pour que les flux s'équilibrent.
3. **Power BI** : visuel Sankey (visuel personnalisé AppSource « Sankey Chart » de Microsoft, à
   ajouter par le propriétaire), première page « Qui fait quoi ? ».
