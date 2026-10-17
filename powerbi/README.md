# Projet Power BI (PBIP)

Le rapport et le modèle sont enregistrés au **format projet Power BI (PBIP)** : modèle
sémantique en **TMDL**, rapport en **PBIR**. Tout est en texte et versionné dans Git.

## Créer le projet (une seule fois, lot 0)

Le squelette PBIP est créé **depuis Power BI Desktop**, pour garantir des fichiers conformes à
ta version de Desktop. Je prends ensuite le relais pour écrire le modèle en TMDL.

1. **Options** (Fichier → Options et paramètres → Options → **Fonctionnalités en préversion**) :
   si elles y figurent encore, coche
   - « Enregistrer le modèle sémantique au format TMDL »,
   - « Stocker les rapports au format de métadonnées amélioré (PBIR) ».
   Redémarre Desktop.
2. Crée les **paramètres** et la **fonction** ci-dessous (Transformer les données → Accueil →
   Gérer les paramètres / Nouvelle source → Requête vide → Éditeur avancé).
3. Crée les requêtes `Dim_Date` et `Dim_Sous_Secteur`, puis **Fermer et appliquer**.
4. Dans le modèle : marque `Dim_Date` comme **table de dates** (colonne `date`).
5. **Fichier → Enregistrer sous** → type **Projet Power BI (*.pbip)**, dans ce dossier `powerbi/`,
   sous le nom **`FinancesPubliques`**. Cela crée :
   ```
   powerbi/FinancesPubliques.pbip
   powerbi/FinancesPubliques.SemanticModel/
   powerbi/FinancesPubliques.Report/
   ```
6. Pousse ces fichiers sur une branche (ou dépose-les via « Add file → Upload files » sur
   GitHub) et ouvre une pull request. Le `.gitignore` exclut déjà les fichiers locaux
   (`.pbi/localSettings.json`, `.pbi/cache.abf`).

## Paramètres Power Query

| Nom | Type | Valeur | Rôle |
|---|---|---|---|
| `ModeSource` | Texte, liste `Local` / `GitHub` | `Local` | Origine des fichiers Parquet (décision D5) |
| `DossierLocal` | Texte | chemin de `data\curated\` dans ton clone, **terminé par `\`** | Mode `Local` |
| `BrancheGitHub` | Texte | `main` | Mode `GitHub` (permet de tester une branche) |

## Fonction `fnLireParquet`

```powerquery
// Lit une table du modèle depuis data/curated, en local ou sur GitHub.
// Web.Contents avec RelativePath : URL de base fixe, indispensable pour l'actualisation
// planifiée dans le service Power BI.
(nomTable as text) as table =>
let
    Contenu =
        if ModeSource = "Local" then
            File.Contents(DossierLocal & nomTable & ".parquet")
        else
            Web.Contents(
                "https://raw.githubusercontent.com",
                [RelativePath = "thcarole1/finances-publiques-france/"
                    & BrancheGitHub & "/data/curated/" & nomTable & ".parquet"]
            ),
    Table = Parquet.Document(Binary.Buffer(Contenu))
in
    Table
```

## Requêtes des tables

```powerquery
// Dim_Date
let Source = fnLireParquet("dim_date") in Source
```

```powerquery
// Dim_Sous_Secteur
let Source = fnLireParquet("dim_sous_secteur") in Source
```

Aucune transformation métier dans Power Query : les types viennent du Parquet, la logique vit
dans `transform/` (dbt).

En mode `GitHub`, choisis l'authentification **Anonyme** pour `https://raw.githubusercontent.com`
(le dépôt est public).
