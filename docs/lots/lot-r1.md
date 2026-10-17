# Lot R1 — Premières pages du rapport

## Livré

| Élément | Détail |
|---|---|
| Pages | Accueil, Combien ?, Qui paie ?, Où va l'argent ?, Qui fait quoi ? (Sankey), Comparer, Glossaire — 1280 × 720, segments Pays/Année synchronisés (France, 2024 par défaut) |
| Glossaire | `docs/glossaire.md` reste la source unique ; `scripts/generer_glossaire.py` en tire `ref_glossaire.csv` → `Dim_Glossaire` ; la CI vérifie la synchronisation. Six nouvelles entrées (dépenses, recettes, PIB, emprunt, lectures légale/économique, fonction) |
| Mesures | En milliards d'euros, en % du PIB, par habitant ; cinq phrases de synthèse (`Phrase : …`) ; titre de sélection |
| Garde-fous | Les mesures de base renvoient vide si plusieurs pays sont sélectionnés (jamais d'addition France + Allemagne) ; le Sankey exige une seule lecture du payeur ; `CG_Unite` ne convertit que les mesures « (M€) » |
| Libellés en clair | « n.c.a. » → « : autres », « R & D » → « Recherche appliquée », TVA et CSG développées, « Excédent de l'année » |
| Contrôles | `scripts/valider_pbir.py` (schémas officiels Microsoft, en CI) ; `tests/test_pbir.py` (champs existants dans le modèle, aucun sigle affiché) |
| Dim_Date | Colonne masquée « Année disponible » : le segment Année ne propose que les années publiées |

## Vérifié (France, 2024)

| Chiffre affiché | Valeur | Référence |
|---|---|---|
| Dépenses publiques | 1 673 Md€, 57,0 % du PIB, 24 321 € par habitant | INSEE : 57,0 % |
| Déficit | 169 Md€, 5,8 % du PIB | INSEE : 5,8 % |
| Qui verse | entreprises 61 €, ménages 31 € sur 100 € de prélèvements | — |
| Qui supporte | ménages environ 86 € sur 100 € | — |
| Sur 1 000 € de dépense | protection sociale 415 €, santé 156 €, services généraux 108 € | — |

## Reporté

- Info-bulles « définition » au survol de chaque indicateur (pages d'info-bulle).
- Repères de crises sur les courbes, thème Power BI versionné (`powerbi/theme.json`).
- Page « La dette » (lot 3).
