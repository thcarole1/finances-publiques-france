# Visuels personnalisés

Visuels compilés à partir de leur code source public, pour pouvoir les importer dans Power BI
Desktop **sans compte professionnel** (AppSource exige un compte professionnel ou scolaire).

| Fichier | Visuel | Source | Version du code | Licence |
|---|---|---|---|---|
| `sankey-3.5.0.0.pbiviz` | Sankey (Microsoft) | https://github.com/microsoft/powerbi-visuals-sankey | commit `4f77de5ed1476b762acc100758ad06a78060f587` | MIT (`LICENSE-sankey.txt`) |

Empreinte SHA-256 de `sankey-3.5.0.0.pbiviz` : `ae7f4cccd21aa303bc04101c22192947d8bf556fe7f3293d4e6a84423eb86800`

Compilation : `npm ci` puis `npx pbiviz package` dans le dépôt source (outils `powerbi-visuals-tools`).

## Importer dans Power BI Desktop

Volet **Visualisations** → **…** (trois points) → **Importer un visuel à partir d'un fichier** →
choisir `powerbi/visuels/sankey-3.5.0.0.pbiviz` → confirmer. L'icône du Sankey apparaît dans le volet.
