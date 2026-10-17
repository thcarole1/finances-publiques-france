# Projet Power BI (PBIP)

Le rapport et le modèle sont enregistrés au **format projet Power BI (PBIP)** : modèle
sémantique en **TMDL**, rapport en **PBIR** (formats par défaut des versions récentes de
Power BI Desktop, rien à activer). Tout est en texte et versionné dans Git.

## Créer le projet (une seule fois, lot 0)

Le squelette est créé **depuis Power BI Desktop**, pour garantir des fichiers conformes à ta
version. On lit les fichiers Parquet **directement sur GitHub** : pas besoin de cloner le dépôt.

### Étape 1 — Ouvrir l'éditeur Power Query

1. Ouvre Power BI Desktop → **Nouveau rapport** (rapport vide).
2. Ruban **Accueil** → **Transformer les données**. L'éditeur Power Query s'ouvre.

### Étape 2 — Créer les 6 requêtes

Pour **chacune** des 6 requêtes du tableau ci-dessous, répète ces gestes :

1. Ruban **Accueil** → **Nouvelle source** → **Requête vide**.
2. Ruban **Accueil** → **Éditeur avancé**.
3. **Efface tout** le texte présent, **colle** le code de la requête, clique **Terminé**.
4. Dans le volet de droite (**Paramètres de la requête → Propriétés → Nom**), renomme la requête
   avec le nom exact du tableau (ou clic droit sur la requête à gauche → **Renommer**).

Crée-les **dans l'ordre** : les dernières utilisent les premières.

| # | Nom exact | Ce que c'est |
|---|---|---|
| 1 | `ModeSource` | Paramètre : lire les fichiers sur `GitHub` ou en `Local` |
| 2 | `DossierLocal` | Paramètre : dossier local (inutilisé tant qu'on est en mode GitHub) |
| 3 | `BrancheGitHub` | Paramètre : branche du dépôt à lire |
| 4 | `fnLireParquet` | Fonction qui lit une table |
| 5 | `Dim_Date` | Table des dates |
| 6 | `Dim_Sous_Secteur` | Table des sous-secteurs |

**Requête 1 — `ModeSource`**

```powerquery
"GitHub" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true, List = {"GitHub", "Local"}, DefaultValue = "GitHub"]
```

**Requête 2 — `DossierLocal`**

```powerquery
"C:\finances-publiques-france\data\curated\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]
```

**Requête 3 — `BrancheGitHub`**

```powerquery
"main" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]
```

**Requête 4 — `fnLireParquet`**

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

**Requête 5 — `Dim_Date`**

```powerquery
let
    Source = fnLireParquet("dim_date")
in
    Source
```

**Requête 6 — `Dim_Sous_Secteur`**

```powerquery
let
    Source = fnLireParquet("dim_sous_secteur")
in
    Source
```

Les requêtes 1 à 3 apparaissent avec une icône de paramètre, la 4 avec une icône de fonction
(*fx*) : c'est normal. Pour les requêtes 1 à 3, fais un clic droit → **décoche « Activer le
chargement »** : sinon Power BI les charge comme de petites tables dans le modèle.

**Si Power Query demande comment se connecter** à `https://raw.githubusercontent.com` : choisis
**Anonyme** → **Se connecter** (le dépôt est public). **S'il demande des niveaux de
confidentialité** : choisis **Public**.

Vérification : clique sur `Dim_Date`, tu dois voir un tableau de dates à partir du 01/01/1990 ;
`Dim_Sous_Secteur` doit afficher 7 lignes (S13, S1311…).

### Étape 3 — Charger et marquer la table de dates

1. Ruban **Accueil** → **Fermer et appliquer**.
2. Dans le volet **Données** à droite, sélectionne la table `Dim_Date` → ruban **Outils de table**
   → **Marquer comme table de dates** → colonne **`date`** → **OK**.

### Étape 4 — Enregistrer au format projet

1. **Fichier → Enregistrer sous** → **Parcourir cet appareil**.
2. Crée un dossier (par exemple `Documents\powerbi-fpf\`).
3. Type : **Projet Power BI (*.pbip)**, nom : **`FinancesPubliques`** → **Enregistrer**.

Vérification : le dossier contient `FinancesPubliques.pbip`, un dossier
`FinancesPubliques.SemanticModel` (avec un sous-dossier `definition` rempli de fichiers `.tmdl`)
et un dossier `FinancesPubliques.Report` (avec un sous-dossier `definition`). S'il y a un fichier
`model.bim` ou `report.json` à la place, ta version utilise encore les anciens formats : signale-le
avant d'envoyer.

### Étape 5 — Envoyer sur GitHub (sans Git installé)

1. Sur GitHub, ouvre le dépôt → dossier **`powerbi`**.
2. **Add file → Upload files**.
3. Glisse-dépose depuis l'Explorateur Windows **le fichier `.pbip` et les deux dossiers**.
4. En bas : choisis **Create a new branch for this commit and start a pull request** → **Propose
   changes** → **Create pull request**.

L'envoi par le site GitHub ignore le `.gitignore` : les fichiers locaux `.pbi/localSettings.json`
et `.pbi/cache.abf` partiront aussi. Pas d'inquiétude, je les retirerai de la branche avant fusion
(ils restent sur ton PC).

## Passer en mode local (plus tard)

Utile quand tu auras cloné le dépôt et voudras tester des données construites sur ton poste :
**Accueil → Gérer les paramètres** → `ModeSource` = `Local`, `DossierLocal` = chemin du dossier
`data\curated\` de ton clone, **terminé par `\`**.

Aucune transformation métier dans Power Query : les types viennent du Parquet, la logique vit
dans `transform/` (dbt).

## Sélecteur « qui paie ? » (paramètre de champ, à créer une fois dans Desktop)

Les paramètres de champ sont créés avec l'assistant de Desktop, qui en écrit une définition
garantie valide (lot 1b).

1. Ruban **Modélisation → Nouveau paramètre → Champs**.
2. Nom : **`FP_Lecture_Payeur`**.
3. Ajouter, dans cet ordre, depuis `Dim_Fonction_Economique` : **Payeur (légal)**,
   **Payeur (économique)**, **Base économique**.
4. Renommer les trois lignes : « Qui verse (lecture légale) », « Qui supporte (lecture économique) »,
   « Base économique ». Laisser cochée l'option d'ajout d'un segment.
5. Créer.

## Diagramme de Sankey « où va l'argent ? » (lot 2b)

Power BI n'a pas de Sankey natif. Le visuel **Sankey** de Microsoft est fourni compilé dans le
dépôt (`powerbi/visuels/`), car AppSource exige un compte professionnel ou scolaire.

1. Volet **Visualisations** → **…** → **Importer un visuel à partir d'un fichier** →
   `powerbi/visuels/sankey-3.5.0.0.pbiviz` (voir `powerbi/visuels/README.md`).
2. Dans le visuel :
   - **Source** : `Pres_Flux_Sankey` › **Source du flux** ;
   - **Destination** : `Pres_Flux_Sankey` › **Destination du flux** ;
   - **Weight** : mesure **Flux (M€)**.
3. Segments indispensables (une seule valeur chacun) : `Dim_Pays` › **Pays**, `Dim_Date` › **Année**,
   `Pres_Flux_Sankey` › **Lecture du payeur**.
4. Facultatif : segment **Étape** pour n'afficher qu'une partie du parcours ; segment
   **CG_Unite › Unité** pour lire les flux en % du PIB ou en € par habitant.
