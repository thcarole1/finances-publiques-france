# Note de reprise

À lire en premier par toute nouvelle session de travail sur ce dépôt.
Dernière mise à jour : 17/10/2026, après le lot 4a (laboratoire en direct).

## 1. Où en est le projet

| Lot | Contenu | État |
|---|---|---|
| 0 | Spécification (`docs/`), outillage, CI, projet Power BI | ✅ fusionné |
| 1 | Socle Eurostat : comptes APU, COFOG × nature, prélèvements, macro, révisions | ✅ fusionné (PR #5) |
| 1b | Qui paie ? Bases économiques (DG TAXUD), lectures légale / économique | ✅ fusionné (PR #6) |
| 2a | Transferts entre administrations (`Fait_Transferts_APU`) | ✅ fusionné (PR #7) |
| 2b | Sankey « où va l'argent ? » (`Pres_Flux_Sankey`) | ✅ fusionné (PR #8) |
| R1 | Rapport : 7 pages du parcours « Comprendre », glossaire, mesures en phrases | ✅ fusionné (PR #9) |
| 3a | Dette annuelle : montant, détenteurs, instruments, coût, effet boule de neige ; pages 6 et 7 | ✅ fusionné (PR #10) |
| 3b | Dette et comptes trimestriels, État / agences (INSEE), dette négociable de l'État, taux et courbe BCE ; pages 8 et 9 | ✅ fusionné (PR #11) |
| 4a | Laboratoire en direct : projection de la dette sur 10 ans, « Et si… ? » ; pages 11 et 12 | PR ouverte (branche `feat/lot-4a-laboratoire`) |
| 4b, 4c | Scénarios sauvegardés (projection Python) ; prévisions officielles et erreurs | à faire |
| 2c | INSEE : détail État/ODAC, prélèvements obligatoires au sens INSEE | en partie : connecteur INSEE et détail État / agences pour la dette (lot 3b) ; reste les comptes annuels et les prélèvements |
| 5 → 8 | redistribution, budgets votés, collectivités, OCDE | à faire (`docs/01-cadrage.md`, § 5) |

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
| Paramètres What-if | Tables calculées `GENERATESERIES` avec `extendedProperty ParameterMetadata` (comme Desktop) ; segment en mode `Single`. Valeur par défaut dans `SELECTEDVALUE` (0 = situation observée) |
| Paramètres Power Query | Créés en requête vide : décocher « Activer le chargement » |
| Rapport (PBIR) | Les fichiers JSON de `powerbi/FinancesPubliques.Report/definition/` sont validés contre les schémas officiels (`scripts/valider_pbir.py`, étape CI) et contre le modèle (`tests/test_pbir.py` : champs existants, aucun sigle affiché). Les pages sont produites par un générateur (non versionné, dans le dossier de travail de la session) ; vérifier avant de régénérer que le générateur reproduit à l'identique les JSON de `main` (`git status` vide), sinon le propriétaire les a retouchées dans Desktop et ce sont **les JSON qui font foi** |
| Phrases (cartes) | Une carte trop petite coupe le texte par « … » au lieu de le faire défiler. Le générateur de pages vérifie, pour chaque phrase, que la plus longue attendue tient dans la carte (police 12 pt). Étalonnage sur Desktop : environ 0,70 × taille de police par caractère, 1,5 × par ligne, 24 px de marge verticale (une phrase de 175 caractères ne tient pas dans 616 × 92). Agrandir la carte ou raccourcir la phrase |
| Dette | Semi-additive : les mesures prennent la dernière fin d'année de la période (`MAX(date_id)`), jamais une somme dans le temps |
| Mesures | On n'additionne jamais des pays : les mesures de base renvoient vide si plusieurs pays sont sélectionnés. `CG_Unite` ne convertit que les mesures dont le nom contient « (M€) » |
| Libellés | Aucun sigle ni code dans un visuel (`docs/09-rapport.md`, § 6) : libellés en clair dans les référentiels, sigles réservés au glossaire |
| Avant chaque envoi | `uv run ruff format . && uv run ruff check . && uv run pytest` (le job `controles` vérifie la mise en forme) |

## 4. Accès réseau

Les noms d'archives des Releases suivent `source__jeu__date.tar.gz` (le jeu peut contenir un tiret :
`dette-trim-apu`). Avant d'ouvrir une PR qui ajoute une source, reconstruire depuis un clone vierge
(données récupérées des Releases) pour reproduire le job CI.

Eurostat refuse une requête entière si un pays n'est pas couvert par le jeu : le collecteur retire
les pays refusés et réessaie (`geos_refuses`).

Domaines autorisés côté session : Eurostat (`ec.europa.eu`), INSEE (`www.insee.fr`, `bdm.insee.fr`),
OCDE, BCE, OFGL, DG TAXUD (`taxation-customs.ec.europa.eu`, `webgate.ec.europa.eu`).
Bloqués constatés : `api.insee.fr`, `www.data.gouv.fr`, `www.aft.gouv.fr` (403). GitHub Actions a
un accès Internet complet : en dernier recours, y faire tourner l'exploration.

## 5. Prochaine étape

Connecteurs disponibles : Eurostat, DG TAXUD, INSEE (BDM, `ingestion/sources/insee.py`, une entrée
par flux dans `JEUX`, séries choisies par IDBANK dans `ref_series_insee.csv`), BCE.

1. **Lot 4b** (scénarios YAML → projection Python → `Fait_Projections`, refinancement selon une
   durée moyenne) ou **4c** (FMI : API datamapper accessible, millésime courant seulement ; Commission
   européenne : AMECO ; gouvernement : saisie manuelle). Le contrôle croisé DAX / Python est prévu
   dans `docs/08`, § 3.
2. **Reste du lot 2c** : comptes annuels de l'État et des organismes (flux INSEE `CNA-2020-CSI`),
   prélèvements obligatoires au sens de l'INSEE (43,2 % contre 42,8 % pour Eurostat en 2024).
3. Échéancier titre par titre : AFT inaccessible depuis la session ; essai depuis GitHub Actions à
   faire.
