"""Génère les pages du rapport Power BI au format PBIR (fichiers JSON de powerbi/…Report).

Usage :
    uv run python scripts/generer_rapport.py

Lit quelques tables préparées (data/curated) et le glossaire (data/reference) : construire les
données avant (./scripts/construire.sh). Réécrit **toutes** les pages : si des pages ont été
retouchées à la main dans Power BI Desktop, ces retouches sont écrasées. Vérifier ensuite avec
`git status` / `git diff` et valider :
    uv run python scripts/valider_pbir.py && uv run pytest tests/test_pbir.py
"""

import hashlib
import json
import shutil
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
RAPPORT = RACINE / "powerbi/FinancesPubliques.Report/definition"
PAGES = RAPPORT / "pages"
V_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json"
P_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SANKEY = "sankey02300D1BE6F5427989F3DE31CCA9E0F32020"
L, H = 1280, 720

BLEU = "#1F4E79"
GRIS = "#595959"
FOND_ENCADRE = "#EEF3F8"


def ident(*parts):
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20]


# --- Expressions -----------------------------------------------------------------------------
def lit(v):
    if isinstance(v, bool):
        val = "true" if v else "false"
    elif isinstance(v, int):
        val = f"{v}L"
    elif isinstance(v, float):
        val = f"{v}D"
    else:
        val = "'" + v.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": val}}}


def couleur(hexa):
    return {"solid": {"color": lit(hexa)}}


def champ(nature, entite, prop):
    return {nature: {"Expression": {"SourceRef": {"Entity": entite}}, "Property": prop}}


def col(entite, prop, **kw):
    return {"kind": "Column", "entite": entite, "prop": prop, **kw}


def mes(prop, entite="_Mesures", **kw):
    return {"kind": "Measure", "entite": entite, "prop": prop, **kw}


def projection(f):
    p = {
        "field": champ(f["kind"], f["entite"], f["prop"]),
        "queryRef": f"{f['entite']}.{f['prop']}",
        "nativeQueryRef": f["prop"],
    }
    if f.get("nom"):
        p["displayName"] = f["nom"]
    if f.get("actif") is not None:
        p["active"] = f["actif"]
    return p


def condition_in(alias, f, valeurs, exclure=False):
    expr = {
        "In": {
            "Expressions": [
                {f["kind"]: {"Expression": {"SourceRef": {"Source": alias}}, "Property": f["prop"]}}
            ],
            "Values": [[lit(v)["expr"]] for v in valeurs],
        }
    }
    if exclure:
        expr = {"Not": {"Expression": expr}}
    return {"Condition": expr}


def filtre(f, valeurs, exclure=False):
    """Définition de filtre (format semanticQuery) sur une colonne, valeurs incluses ou exclues."""
    alias = f["entite"][0].lower()
    return {
        "Version": 2,
        "From": [{"Name": alias, "Entity": f["entite"], "Type": 0}],
        "Where": [condition_in(alias, f, valeurs, exclure)],
    }


def filtre_visuel(nom, f, valeurs, exclure=False):
    return {
        "name": nom,
        "field": champ(f["kind"], f["entite"], f["prop"]),
        "type": "Categorical",
        "filter": filtre(f, valeurs, exclure),
        "howCreated": "User",
        "isHiddenInViewMode": True,
    }


# --- Visuels ---------------------------------------------------------------------------------
class Page:
    def __init__(self, nom, titre, question, infobulle=False, largeur=None, hauteur=None):
        self.nom, self.titre, self.question = nom, titre, question
        self.visuels, self.interactions = [], []
        self.infobulle = infobulle
        self.largeur, self.hauteur = largeur or L, hauteur or H

    def visuel(self, cle):
        nom = ident(self.nom, cle)
        return next(v for v in self.visuels if v["name"] == nom)

    def ajouter(
        self,
        cle,
        type_visuel,
        x,
        y,
        w,
        h,
        roles=None,
        objets=None,
        conteneur=None,
        filtres=None,
        tri=None,
        sync=None,
    ):
        nom = ident(self.nom, cle)
        visuel = {"visualType": type_visuel}
        if roles:
            visuel["query"] = {
                "queryState": {
                    r: {"projections": [projection(f) for f in fs]} for r, fs in roles.items()
                }
            }
            if tri:
                f, sens = tri
                visuel["query"]["sortDefinition"] = {
                    "sort": [
                        {"field": champ(f["kind"], f["entite"], f["prop"]), "direction": sens}
                    ],
                    "isDefaultSort": False,
                }
        if objets:
            visuel["objects"] = objets
        if conteneur:
            visuel["visualContainerObjects"] = conteneur
        if sync:
            visuel["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
        visuel["drillFilterOtherVisuals"] = True
        doc = {
            "$schema": V_SCHEMA,
            "name": nom,
            "position": {
                "x": x,
                "y": y,
                "z": len(self.visuels) * 1000,
                "height": h,
                "width": w,
                "tabOrder": len(self.visuels) * 1000,
            },
            "visual": visuel,
        }
        if filtres:
            doc["filterConfig"] = {"filters": filtres}
        self.visuels.append(doc)
        return nom

    def sans_filtre(self, source, cibles):
        for c in cibles:
            self.interactions.append({"source": source, "target": c, "type": "NoFilter"})


def titre_visuel(texte, taille=12):
    return {
        "title": [
            {
                "properties": {
                    "show": lit(True),
                    "text": lit(texte),
                    "fontSize": lit(float(taille)),
                    "fontColor": couleur(BLEU),
                    "bold": lit(True),
                    "titleWrap": lit(True),
                }
            }
        ],
    }


def sans_titre():
    return {"title": [{"properties": {"show": lit(False)}}]}


def fond(hexa):
    return {
        "background": [
            {"properties": {"show": lit(True), "color": couleur(hexa), "transparency": lit(0.0)}}
        ]
    }


def texte(page, cle, x, y, w, h, paragraphes, fond_couleur=None):
    """Zone de texte. paragraphes : liste de listes de (texte, style) ou de chaînes."""
    pars = []
    for p in paragraphes:
        runs = []
        for r in p if isinstance(p, list) else [p]:
            valeur, style = (r, {}) if isinstance(r, str) else r
            ts = {"fontSize": style.get("taille", "11pt"), "color": style.get("couleur", GRIS)}
            if style.get("gras"):
                ts["fontWeight"] = "bold"
            runs.append({"value": valeur, "textStyle": ts})
        pars.append({"textRuns": runs})
    conteneur = {}
    if fond_couleur:
        conteneur.update(fond(fond_couleur))
    return page.ajouter(
        cle,
        "textbox",
        x,
        y,
        w,
        h,
        objets={"general": [{"properties": {"paragraphs": pars}}]},
        conteneur=conteneur or None,
    )


def comprendre(page, x, y, w, h, lignes, source=None):
    pars = [[("Comprendre", {"gras": True, "taille": "12pt", "couleur": BLEU})]]
    pars += [[(ligne, {})] for ligne in lignes]
    if source:
        pars.append([(source, {"taille": "9pt"})])
    return texte(page, "comprendre", x, y, w, h, pars, FOND_ENCADRE)


def carte(page, cle, x, y, w, h, mesure, titre, taille=26):
    # Titre (11 pt, sur une ou plusieurs lignes) + valeur : la carte doit contenir les deux.
    lignes_titre = lignes_necessaires(titre, w, 11, facteur=0.55, marge=16)
    besoin = 16 + lignes_titre * 20 + 1.25 * taille * 4 / 3
    if lignes_titre > 2 or besoin > h:
        TROP_PETITES.append(
            (
                page.titre,
                f"carte « {titre} »",
                f"{lignes_titre} ligne(s) de titre",
                round(besoin),
                w,
                h,
            )
        )
    return page.ajouter(
        cle,
        "card",
        x,
        y,
        w,
        h,
        roles={"Values": [mes(mesure)]},
        objets={
            "labels": [{"properties": {"fontSize": lit(float(taille)), "color": couleur(BLEU)}}],
            "categoryLabels": [{"properties": {"show": lit(False)}}],
        },
        conteneur=titre_visuel(titre, 11),
    )


TAILLE_PHRASE = 12  # points
TROP_PETITES = []

# Phrase la plus longue attendue pour chaque mesure (France, années récentes) : sert à vérifier
# que la carte est assez grande. Une carte trop petite coupe le texte par « … ».
EXEMPLES = {
    "Phrase : scénarios": "En 2035, la dette atteindrait 129 % de la richesse produite dans le scénario « Exemple : "
    "effort de 0,5 point par an », contre 145 % si la situation actuelle se prolonge (15 points de moins).",
    "Phrase : dernière prévision": "Dernière prévision publiée (Commission – printemps 2026) pour « Dette "
    "publique (% du PIB) » : 118,5 % en 2026, 120,4 % en 2027, 121,7 % en 2028.",
    "Phrase : biais des prévisions": "Pour l'année suivante, les prévisions de la Commission européenne sur "
    "« Solde public (% du PIB) » ont été en moyenne trop optimistes de 0,6 point (33 prévisions comparées). "
    "L'erreur moyenne, dans un sens ou dans l'autre, est de 1,0 point.",
    "Phrase : projection": "Avec une croissance de 1,0 % par an, une inflation de 1,8 %, un taux moyen de "
    "2,0 % et un déficit hors intérêts de 2,9 % de la richesse produite, la dette passerait de 116 % en "
    "2025 à 135 % en 2035. Pour la stabiliser, il faudrait un déficit hors intérêts d'au plus 0,9 %.",
    "Phrase : simulation": "Avec ces mesures, le solde public de 2025 passerait de -5,4 % à -4,6 % de la "
    "richesse produite (+24 milliards d'euros, soit +350 € par habitant).",
    "Phrase : combien ?": "En 2024, les administrations publiques ont dépensé 1 673 milliards d'euros, soit 57 € "
    "pour 100 € de richesse produite dans le pays, ou 24 321 € par habitant.",
    "Phrase : solde": "Les recettes (1 504 milliards d'euros) n'ont pas suffi : il a fallu emprunter 169 "
    "milliards d'euros. C'est le déficit public, égal à 5,8 % de la richesse produite.",
    "Phrase : qui paie ?": "Sur 100 € d'impôts et de cotisations, les entreprises en versent 61 € et les "
    "ménages 31 €. Mais une fois les coûts répercutés sur les prix et les salaires, les ménages en "
    "supportent environ 86 €.",
    "Phrase : où va l'argent ?": "Sur 1 000 € de dépense publique, les trois premiers postes sont : "
    "Protection sociale (415 €), Santé (156 €), Services généraux (108 €).",
    "Phrase : comparaison": "En 2024, la dépense publique représente 57,0 % de la richesse produite pour "
    "le pays « France » : rang 1 sur 29 pays comparés (1 = dépense la plus élevée).",
    "Phrase : dette": "Fin 2024, la dette publique atteint 3 306 milliards d'euros, soit 113 % de la "
    "richesse produite en un an, ou 48 070 € par habitant. Ses intérêts ont coûté 60 milliards "
    "d'euros dans l'année, soit un taux moyen de 1,9 %.",
    "Phrase : boule de neige": "En 2025, le taux moyen payé sur la dette (2,0 %) est supérieur à la "
    "croissance de l'économie (1,9 %) : la dette grossit d'elle-même (effet boule de neige). Sur "
    "l'année, elle a augmenté de 3,1 points de richesse produite, dont 2,9 points dus au déficit hors intérêts.",
    "Phrase : détenteurs": "Fin 2024, 53 % de la dette est détenue par des investisseurs étrangers, 19 % "
    "par la banque centrale et 28 % par les autres prêteurs du pays (banques, assureurs, ménages…).",
    "Phrase : dette trimestrielle": "Au 2e trimestre 2026, la dette publique atteint 3 596 milliards "
    "d'euros (119,1 % de la richesse produite sur un an). En un an, elle a augmenté de 178 milliards "
    "d'euros, soit environ 488 millions d'euros par jour.",
    "Phrase : taux": "En 2025, l'État a emprunté à 10 ans au taux moyen de 3,4 %, soit 0,76 point de plus "
    "que l'Allemagne. 11 % des titres de l'État sont indexés sur l'inflation : leur coût suit la hausse "
    "des prix.",
}


def lignes_necessaires(texte, largeur, taille=TAILLE_PHRASE, facteur=0.70, marge=32):
    """Estimation prudente du nombre de lignes (police Segoe UI, mots entiers). Le facteur et la
    marge des valeurs de carte sont plus élevés que ceux des titres (marges internes du visuel)."""
    px = taille * 4 / 3
    car_par_ligne = int((largeur - marge) / (facteur * px))
    lignes, courante = 1, 0
    for mot in texte.split():
        if courante and courante + 1 + len(mot) > car_par_ligne:
            lignes, courante = lignes + 1, len(mot)
        else:
            courante += (1 if courante else 0) + len(mot)
    return lignes


def phrase(page, cle, x, y, w, h, mesure):
    """Carte affichant une mesure de texte (une phrase), sur plusieurs lignes."""
    px = TAILLE_PHRASE * 4 / 3
    lignes_dispo = int((h - 24) / (1.5 * px))
    besoin = lignes_necessaires(EXEMPLES[mesure], w)
    if besoin > lignes_dispo:
        TROP_PETITES.append((page.titre, mesure, besoin, lignes_dispo, w, h))
    return page.ajouter(
        cle,
        "card",
        x,
        y,
        w,
        h,
        roles={"Values": [mes(mesure)]},
        objets={
            "labels": [
                {"properties": {"fontSize": lit(float(TAILLE_PHRASE)), "color": couleur("#262626")}}
            ],
            "categoryLabels": [{"properties": {"show": lit(False)}}],
            "wordWrap": [{"properties": {"show": lit(True)}}],
        },
        conteneur=sans_titre(),
    )


def en_tete(page, pays=True, annee=True, lecture=False):
    page.ajouter("navigation", "pageNavigator", 16, 8, L - 32, 40, conteneur=sans_titre())
    texte(
        page,
        "titre",
        16,
        54,
        820,
        62,
        [
            [(page.question, {"gras": True, "taille": "20pt", "couleur": BLEU})],
        ],
    )
    slicers = {}
    x = L - 16
    if annee:
        x -= 170
        slicers["annee"] = page.ajouter(
            "segment_annee",
            "slicer",
            x,
            54,
            170,
            62,
            roles={"Values": [col("Dim_Date", "Année")]},
            tri=(col("Dim_Date", "Année"), "Descending"),
            objets={
                "data": [{"properties": {"mode": lit("Dropdown")}}],
                "selection": [
                    {
                        "properties": {
                            "strictSingleSelect": lit(True),
                            "singleSelect": lit(True),
                            "selectAllCheckboxEnabled": lit(False),
                        }
                    }
                ],
                "general": [
                    {"properties": {"filter": {"filter": filtre(col("Dim_Date", "Année"), [2024])}}}
                ],
                "header": [{"properties": {"show": lit(True), "text": lit("Année")}}],
            },
            filtres=[
                filtre_visuel(
                    ident(page.nom, "f_annee"), col("Dim_Date", "Année disponible"), [True]
                )
            ],
            sync="Année",
        )
    if pays:
        x -= 196
        slicers["pays"] = page.ajouter(
            "segment_pays",
            "slicer",
            x,
            54,
            180,
            62,
            roles={"Values": [col("Dim_Pays", "Pays")]},
            objets={
                "data": [{"properties": {"mode": lit("Dropdown")}}],
                "selection": [
                    {
                        "properties": {
                            "strictSingleSelect": lit(True),
                            "singleSelect": lit(True),
                            "selectAllCheckboxEnabled": lit(False),
                        }
                    }
                ],
                "general": [
                    {
                        "properties": {
                            "filter": {"filter": filtre(col("Dim_Pays", "Pays"), ["France"])}
                        }
                    }
                ],
                "header": [{"properties": {"show": lit(True), "text": lit("Pays")}}],
            },
            filtres=[
                filtre_visuel(
                    ident(page.nom, "f_pays"), col("Dim_Pays", "Code pays"), ["_NA"], exclure=True
                )
            ],
            sync="Pays",
        )
    if lecture:
        x -= 296
        slicers["lecture"] = page.ajouter(
            "segment_lecture",
            "slicer",
            x,
            54,
            280,
            62,
            roles={"Values": [col("Pres_Flux_Sankey", "Lecture du payeur")]},
            objets={
                "data": [{"properties": {"mode": lit("Dropdown")}}],
                "selection": [
                    {
                        "properties": {
                            "strictSingleSelect": lit(True),
                            "singleSelect": lit(True),
                            "selectAllCheckboxEnabled": lit(False),
                        }
                    }
                ],
                "general": [
                    {
                        "properties": {
                            "filter": {
                                "filter": filtre(
                                    col("Pres_Flux_Sankey", "Lecture du payeur"),
                                    ["Qui supporte (lecture économique)"],
                                )
                            }
                        }
                    }
                ],
                "header": [{"properties": {"show": lit(True), "text": lit("Qui paie ?")}}],
            },
        )
    return slicers


def barres(
    page,
    cle,
    x,
    y,
    w,
    h,
    categorie,
    mesure,
    titre,
    type_visuel="clusteredBarChart",
    tri=True,
    couleur_barres=BLEU,
):
    return page.ajouter(
        cle,
        type_visuel,
        x,
        y,
        w,
        h,
        roles={"Category": [categorie], "Y": [mes(mesure)]},
        tri=(mes(mesure), "Descending") if tri else None,
        objets={
            "labels": [{"properties": {"show": lit(True)}}],
            "dataPoint": [{"properties": {"fill": couleur(couleur_barres)}}],
            "categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
            "valueAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False)}}],
        },
        conteneur=titre_visuel(titre),
    )


Y0 = 128  # début de la zone de contenu

# --- Page 1 : Accueil -------------------------------------------------------------------------
p1 = Page("7756ddd2f312a291b3a8", "1. Accueil", "L'argent public en un coup d'œil")
s = en_tete(p1)
texte(
    p1,
    "intro",
    16,
    Y0,
    L - 32,
    44,
    [
        "Ce rapport répond à des questions simples sur l'argent public. Choisissez un pays et une année en haut "
        "à droite, puis une question dans le sommaire. Les montants sont consolidés : un euro versé par l'État à "
        "une commune n'est compté qu'une fois. Survolez un chiffre pour voir sa définition.",
    ],
)
cw, gap = (L - 32 - 3 * 16) / 4, 16
for i, (m, t) in enumerate(
    [
        ("Dépenses publiques (Md€)", "Dépenses publiques de l'année"),
        ("Recettes publiques (Md€)", "Recettes publiques de l'année"),
        ("Solde public (Md€)", "Solde (négatif : déficit)"),
        ("Dépenses publiques par habitant (€)", "Dépense publique par habitant"),
    ]
):
    carte(p1, f"carte{i}", 16 + i * (cw + gap), Y0 + 52, cw, 96, m, t)
phrase(p1, "phrase_combien", 16, Y0 + 156, L - 32, 72, "Phrase : combien ?")
phrase(p1, "phrase_solde", 16, Y0 + 232, L - 32, 72, "Phrase : solde")
texte(
    p1,
    "sommaire_titre",
    16,
    Y0 + 312,
    L - 32,
    28,
    [
        [
            (
                "Sommaire : cliquez sur une question",
                {"gras": True, "taille": "12pt", "couleur": BLEU},
            )
        ],
    ],
)

# --- Page 2 : Combien ? -----------------------------------------------------------------------
p2 = Page(
    ident("page", "combien"), "2. Combien ?", "Quel poids pèse l'argent public dans l'économie ?"
)
s = en_tete(p2)
lc = p2.ajouter(
    "courbes",
    "lineChart",
    16,
    Y0,
    820,
    290,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Y": [
            mes("Dépenses publiques (% PIB)", nom="Dépenses"),
            mes("Recettes publiques (% PIB)", nom="Recettes"),
        ],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel(
        "Dépenses et recettes publiques chaque année, en % de la richesse produite"
    ),
)
cc = p2.ajouter(
    "solde",
    "clusteredColumnChart",
    16,
    Y0 + 302,
    820,
    H - Y0 - 302 - 16,
    roles={"Category": [col("Dim_Date", "Année")], "Y": [mes("Solde public (% PIB)", nom="Solde")]},
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "dataPoint": [{"properties": {"fill": couleur("#C0504D")}}],
    },
    conteneur=titre_visuel(
        "Solde public chaque année, en % de la richesse produite (sous zéro : déficit)"
    ),
)
p2.sans_filtre(s["annee"], [lc, cc])
carte(
    p2,
    "pour100",
    852,
    Y0,
    L - 852 - 16,
    104,
    "Sur 100 € de richesse produite",
    "Dépense publique pour 100 € de richesse produite (année choisie)",
)
carte(
    p2,
    "taux_po",
    852,
    Y0 + 116,
    L - 852 - 16,
    104,
    "Taux de prélèvements obligatoires",
    "Impôts et cotisations, en % de la richesse produite (année choisie)",
)
comprendre(
    p2,
    852,
    Y0 + 232,
    L - 852 - 16,
    H - Y0 - 232 - 16,
    [
        "La richesse produite (le PIB) sert d'étalon : elle permet de comparer les années entre elles, malgré "
        "l'inflation et la croissance.",
        "Les pics de 2009 et 2020 correspondent aux crises : la dépense augmente (chômage partiel, aides) au "
        "moment où la richesse produite recule, ce qui gonfle le ratio.",
        "Quand la courbe des dépenses passe au-dessus de celle des recettes, l'écart est le déficit, financé "
        "par l'emprunt.",
    ],
    source="Source : Eurostat.",
)

# --- Page 3 : Qui paie ? ----------------------------------------------------------------------
p3 = Page(ident("page", "qui_paie"), "3. Qui paie ?", "D'où vient l'argent public ?")
s = en_tete(p3)
barres(
    p3,
    "legal",
    16,
    Y0,
    616,
    264,
    col("Dim_Fonction_Economique", "Payeur (légal)"),
    "Prélèvements par payeur (Md€)",
    "Qui verse les impôts et cotisations ? (en milliards d'euros)",
)
barres(
    p3,
    "eco",
    648,
    Y0,
    L - 648 - 16,
    264,
    col("Dim_Fonction_Economique", "Payeur (économique)"),
    "Prélèvements par payeur (Md€)",
    "Qui en supporte finalement le coût ? (estimation, en milliards d'euros)",
    couleur_barres="#2E75B6",
)
p3.ajouter(
    "assiette",
    "treemap",
    16,
    Y0 + 276,
    616,
    H - Y0 - 276 - 16,
    roles={
        "Group": [col("Dim_Prelevement", "Assiette")],
        "Values": [mes("Prélèvements obligatoires (Md€)")],
    },
    objets={
        "labels": [{"properties": {"show": lit(True)}}],
        "legend": [{"properties": {"show": lit(False)}}],
    },
    conteneur=titre_visuel("Sur quoi portent les impôts et cotisations ? (en milliards d'euros)"),
)
phrase(p3, "phrase", 648, Y0 + 276, L - 648 - 16, 144, "Phrase : qui paie ?")
comprendre(
    p3,
    648,
    Y0 + 428,
    L - 648 - 16,
    H - Y0 - 428 - 16,
    [
        "Qui verse : celui qui transfère l'argent au fisc ou aux caisses de Sécurité sociale. Par exemple, "
        "le commerçant reverse la taxe sur la valeur ajoutée payée par ses clients.",
        "Qui supporte : celui dont le revenu baisse réellement, une fois les prix et les salaires ajustés. "
        "Cette lecture repose sur des hypothèses courantes chez les économistes : c'est un ordre de grandeur.",
    ],
    source="Sources : Eurostat ; Commission européenne, listes nationales des impôts.",
)

# --- Page 4 : Où va l'argent ? ----------------------------------------------------------------
p4 = Page(ident("page", "ou_va"), "4. Où va l'argent ?", "À quoi sert la dépense publique ?")
s = en_tete(p4)
barres(
    p4,
    "fonctions",
    16,
    Y0,
    700,
    430,
    col("Dim_COFOG", "Fonction"),
    "Pour 1 000 € de dépense publique",
    "Sur 1 000 € de dépense publique, combien pour chaque domaine ?",
)
p4.ajouter(
    "detail",
    "pivotTable",
    732,
    Y0,
    L - 732 - 16,
    430,
    roles={
        "Rows": [col("Dim_COFOG", "Fonction"), col("Dim_COFOG", "Sous-fonction")],
        "Values": [
            mes("Dépenses par fonction (Md€)", nom="Milliards d'euros"),
            mes("Pour 1 000 € de dépense publique", nom="Sur 1 000 €"),
        ],
    },
    tri=(mes("Dépenses par fonction (Md€)"), "Descending"),
    objets={"rowHeaders": [{"properties": {"wordWrap": lit(True)}}]},
    conteneur=titre_visuel("Le détail par domaine (cliquez sur + pour déplier)"),
)
phrase(p4, "phrase", 16, Y0 + 442, 700, H - Y0 - 442 - 16, "Phrase : où va l'argent ?")
comprendre(
    p4,
    732,
    Y0 + 442,
    L - 732 - 16,
    H - Y0 - 442 - 16,
    [
        "La protection sociale comprend les retraites, les allocations familiales, l'assurance chômage et la "
        "lutte contre la pauvreté ; la santé, l'hôpital et les remboursements de soins.",
        "Les « services généraux » comprennent notamment les intérêts de la dette.",
    ],
    source="Source : Eurostat, dépenses par fonction (classification internationale COFOG).",
)

# --- Page 5 : Qui fait quoi ? -----------------------------------------------------------------
p5 = Page(ident("page", "qui_fait_quoi"), "5. Qui fait quoi ?", "Qui encaisse, qui dépense ?")
s = en_tete(p5, lecture=True)
p5.ajouter(
    "sankey",
    SANKEY,
    16,
    Y0,
    860,
    H - Y0 - 16,
    roles={
        "Source": [col("Pres_Flux_Sankey", "Source du flux")],
        "Destination": [col("Pres_Flux_Sankey", "Destination du flux")],
        "Weight": [mes("Flux (Md€)")],
    },
    conteneur=titre_visuel(
        "Le circuit de l'argent public, de gauche à droite (en milliards d'euros)"
    ),
)
p5.ajouter(
    "transferts",
    "pivotTable",
    892,
    Y0,
    L - 892 - 16,
    236,
    roles={
        "Rows": [col("Dim_Sous_Secteur", "Sous-secteur (court)", nom="Qui verse")],
        "Columns": [
            col("Dim_Sous_Secteur_Receveur", "Sous-secteur receveur (court)", nom="Qui reçoit")
        ],
        "Values": [mes("Transferts entre administrations (Md€)", nom="Milliards d'euros")],
    },
    conteneur=titre_visuel("Les versements entre administrations (en milliards d'euros)"),
)
comprendre(
    p5,
    892,
    Y0 + 248,
    L - 892 - 16,
    H - Y0 - 248 - 16,
    [
        "Lisez le diagramme de gauche à droite : qui paie (ménages, entreprises, emprunt), quelle "
        "administration encaisse, laquelle dépense après les versements entre elles, puis à quoi sert l'argent.",
        "La largeur de chaque flux est proportionnelle au montant. Le choix « Qui paie ? » en haut bascule entre "
        "« qui verse » et « qui supporte » les prélèvements.",
        "Si le diagramme ne s'affiche pas, importez le visuel une fois (voir le guide du dossier powerbi).",
    ],
)

# --- Page 6 : La dette ----------------------------------------------------------------------
pd = Page(
    ident("page", "dette"), "6. La dette", "Combien doit-on, et pourquoi la dette augmente-t-elle ?"
)
s = en_tete(pd)
cw4 = (L - 32 - 3 * 16) / 4
for i, (m, t) in enumerate(
    [
        ("Dette publique (Md€)", "Dette publique en fin d'année"),
        ("Dette publique (% PIB)", "Dette rapportée à la richesse"),
        ("Dette publique par habitant (€)", "Dette par habitant"),
        ("Taux moyen payé sur la dette", "Taux moyen payé sur la dette"),
    ]
):
    carte(pd, f"carte{i}", 16 + i * (cw4 + 16), Y0, cw4, 88, m, t)
ld = pd.ajouter(
    "ratio",
    "lineChart",
    16,
    Y0 + 100,
    400,
    244,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Y": [mes("Dette publique (% PIB)", nom="Dette")],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "dataPoint": [{"properties": {"fill": couleur(BLEU)}}],
    },
    conteneur=titre_visuel("Dette publique en fin d'année, en % de la richesse produite"),
)
cd = pd.ajouter(
    "decomposition",
    "columnChart",
    432,
    Y0 + 100,
    420,
    244,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Y": [
            mes("Déficit hors intérêts (points de PIB)", nom="Déficit hors intérêts"),
            mes("Effet boule de neige (points de PIB)", nom="Écart entre taux et croissance"),
            mes("Autres facteurs (points de PIB)", nom="Autres facteurs"),
        ],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel("Pourquoi la dette varie chaque année (en points de richesse produite)"),
)
pd.sans_filtre(s["annee"], [ld, cd])
phrase(pd, "phrase_dette", 16, Y0 + 356, L - 32, 96, "Phrase : dette")
phrase(pd, "phrase_boule", 16, Y0 + 460, L - 32, H - Y0 - 460 - 16, "Phrase : boule de neige")
comprendre(
    pd,
    868,
    Y0 + 100,
    L - 868 - 16,
    244,
    [
        "Le graphique de droite sépare trois causes de la variation de la dette : le déficit hors intérêts, "
        "l'écart entre le taux payé et la croissance, et des opérations de trésorerie.",
        "Quand la croissance dépasse le taux payé, le poids de la dette baisse tout seul.",
    ],
    source="Source : Eurostat, dette notifiée à la Commission européenne.",
)

# --- Page 7 : À qui doit-on ? -----------------------------------------------------------------
pq = Page(
    ident("page", "a_qui"), "7. À qui doit-on ?", "Qui prête aux administrations, et à quel prix ?"
)
s = en_tete(pq)
barres(
    pq,
    "detenteurs",
    16,
    Y0,
    616,
    280,
    col("Dim_Detenteur", "Détenteur"),
    "Dette par détenteur (Md€)",
    "Qui détient la dette ? (en milliards d'euros, fin d'année)",
)
barres(
    pq,
    "instruments",
    648,
    Y0,
    L - 648 - 16,
    280,
    col("Dim_Instrument_Dette", "Instrument (court)"),
    "Dette par instrument (Md€)",
    "Sous quelle forme emprunte-t-on ? (en milliards d'euros, fin d'année)",
    couleur_barres="#2E75B6",
)
lt = pq.ajouter(
    "taux",
    "lineChart",
    16,
    Y0 + 292,
    616,
    H - Y0 - 292 - 16,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Y": [
            mes("Taux d'emprunt à 10 ans", nom="Taux des nouveaux emprunts à 10 ans"),
            mes("Taux moyen payé sur la dette", nom="Taux moyen payé sur toute la dette"),
        ],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel("Le coût de l'emprunt chaque année"),
)
pq.sans_filtre(s["annee"], [lt])
phrase(pq, "phrase", 648, Y0 + 292, L - 648 - 16, 120, "Phrase : détenteurs")
comprendre(
    pq,
    648,
    Y0 + 420,
    L - 648 - 16,
    H - Y0 - 420 - 16,
    [
        "L'État emprunte surtout en émettant des obligations, achetées par des banques, des assureurs (via "
        "l'assurance vie), la banque centrale et des investisseurs étrangers.",
        "Le taux moyen payé suit les taux du marché avec retard : les anciens emprunts gardent leur taux "
        "d'origine. Détail par détenteur publié depuis 2020 pour la plupart des pays.",
    ],
    source="Source : Eurostat (dette par détenteur, taux à long terme).",
)

# --- Page 8 : Les derniers trimestres --------------------------------------------------------
pt = Page(
    ident("page", "trimestres"), "8. Les derniers trimestres", "Où en est la dette aujourd'hui ?"
)
s = en_tete(pt, annee=False)
cw4 = (L - 32 - 3 * 16) / 4
cartes_t = [
    ("Dernier trimestre connu", "Dernier trimestre publié"),
    ("Dette au dernier trimestre connu (Md€)", "Dette publique à cette date"),
    ("Dette au dernier trimestre connu (% PIB)", "Dette rapportée à la richesse"),
    ("Hausse de la dette sur un an (Md€)", "Variation de la dette en un an"),
]
for i, (m, t) in enumerate(cartes_t):
    carte(pt, f"carte{i}", 16 + i * (cw4 + 16), Y0, cw4, 88, m, t, taille=20 if i == 0 else 26)
AXE_T = {
    "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}],
    "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
}
pt.ajouter(
    "ratio",
    "lineChart",
    16,
    Y0 + 100,
    620,
    250,
    roles={
        "Category": [col("Dim_Date", "Année-trimestre")],
        "Y": [mes("Dette trimestrielle (% PIB)", nom="Dette")],
    },
    tri=(col("Dim_Date", "Année-trimestre"), "Ascending"),
    objets={**AXE_T, "dataPoint": [{"properties": {"fill": couleur(BLEU)}}]},
    conteneur=titre_visuel("Dette en fin de trimestre, en % de la richesse produite sur un an"),
)
pt.ajouter(
    "solde",
    "clusteredColumnChart",
    16,
    Y0 + 362,
    620,
    H - Y0 - 362 - 16,
    roles={
        "Category": [col("Dim_Date", "Année-trimestre")],
        "Y": [mes("Solde trimestriel (% PIB)", nom="Solde")],
    },
    tri=(col("Dim_Date", "Année-trimestre"), "Ascending"),
    objets={**AXE_T, "dataPoint": [{"properties": {"fill": couleur("#C0504D")}}]},
    conteneur=titre_visuel(
        "Solde public de chaque trimestre, corrigé des variations saisonnières (sous zéro : déficit)"
    ),
)
pt.ajouter(
    "contributions",
    "columnChart",
    652,
    Y0 + 100,
    L - 652 - 16,
    220,
    roles={
        "Category": [col("Dim_Date", "Année-trimestre")],
        "Series": [col("Dim_Sous_Secteur", "Sous-secteur (court)", nom="Administration")],
        "Y": [mes("Contribution à la dette (Md€)", nom="Milliards d'euros")],
    },
    tri=(col("Dim_Date", "Année-trimestre"), "Ascending"),
    objets={**AXE_T, "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}]},
    conteneur=titre_visuel(
        "France : quelle administration porte la dette ? (en milliards d'euros)"
    ),
)
phrase(pt, "phrase", 652, Y0 + 332, L - 652 - 16, 144, "Phrase : dette trimestrielle")
comprendre(
    pt,
    652,
    Y0 + 484,
    L - 652 - 16,
    H - Y0 - 484 - 16,
    [
        "La dette est mesurée chaque trimestre, ce qui permet de suivre l'année en cours. Pour la France, "
        "l'INSEE publie environ trois mois avant Eurostat.",
        "L'État porte l'essentiel de la dette : les collectivités locales et la Sécurité sociale empruntent peu.",
    ],
    source="Sources : INSEE (France), Eurostat (autres pays).",
)

# --- Page 9 : Les taux d'intérêt --------------------------------------------------------------
pr = Page(ident("page", "taux"), "9. Les taux d'intérêt", "À quel prix les États empruntent-ils ?")
s = en_tete(pr)
AXE = {
    "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}],
    "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
    "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
}
l1 = pr.ajouter(
    "dix_ans",
    "lineChart",
    16,
    Y0,
    620,
    290,
    roles={
        "Category": [col("Dim_Date", "Année-mois")],
        "Y": [
            mes("Taux d'emprunt à 10 ans", nom="Pays choisi"),
            mes("Taux à 10 ans de l'Allemagne", nom="Allemagne"),
        ],
    },
    tri=(col("Dim_Date", "Année-mois"), "Ascending"),
    objets=AXE,
    conteneur=titre_visuel("Taux des emprunts d'État à 10 ans, chaque mois"),
)
l2 = pr.ajouter(
    "ecart",
    "lineChart",
    16,
    Y0 + 302,
    620,
    H - Y0 - 302 - 16,
    roles={
        "Category": [col("Dim_Date", "Année-mois")],
        "Y": [mes("Écart de taux avec l'Allemagne (points)", nom="Écart")],
    },
    tri=(col("Dim_Date", "Année-mois"), "Ascending"),
    objets={
        **AXE,
        "legend": [{"properties": {"show": lit(False)}}],
        "dataPoint": [{"properties": {"fill": couleur("#C0504D")}}],
    },
    conteneur=titre_visuel("Écart de taux avec l'Allemagne (en points)"),
)
cb = pr.ajouter(
    "courbe",
    "lineChart",
    652,
    Y0,
    L - 652 - 16,
    250,
    roles={
        "Category": [col("Fait_Courbe_Taux", "Maturité (ans)")],
        "Y": [
            mes("Courbe des taux (fin de l'année choisie)", nom="Année choisie"),
            mes("Courbe des taux (un an plus tôt)", nom="Un an plus tôt"),
        ],
    },
    tri=(col("Fait_Courbe_Taux", "Maturité (ans)"), "Ascending"),
    objets=AXE,
    conteneur=titre_visuel(
        "Zone euro : taux d'emprunt des États selon la durée du prêt (en années)"
    ),
)
pr.sans_filtre(s["annee"], [l1, l2])
pr.sans_filtre(s["pays"], [cb])
cw2 = (L - 652 - 16 - 16) / 2
carte(
    pr,
    "indexee",
    652,
    Y0 + 262,
    cw2,
    88,
    "Part indexée sur l'inflation (%)",
    "État : dette indexée sur les prix",
    taille=22,
)
carte(
    pr,
    "court",
    652 + cw2 + 16,
    Y0 + 262,
    cw2,
    88,
    "Part à court terme (%)",
    "État : part à un an ou moins",
    taille=22,
)
phrase(pr, "phrase", 652, Y0 + 362, L - 652 - 16, 120, "Phrase : taux")
comprendre(
    pr,
    652,
    Y0 + 490,
    L - 652 - 16,
    H - Y0 - 490 - 16,
    [
        "L'Allemagne, jugée l'emprunteur le plus sûr de la zone euro, sert de référence. Plus on prête "
        "longtemps, plus le taux est en général élevé : c'est la « courbe des taux ».",
    ],
    source="Sources : Eurostat (taux à 10 ans), Banque centrale européenne (courbe), INSEE (dette de l'État).",
)

# --- Page 10 : Comparer ------------------------------------------------------------------------
p6 = Page(
    ident("page", "comparer"), "10. Comparer", "La France dépense-t-elle plus que ses voisins ?"
)
s = en_tete(p6)
b1 = barres(
    p6,
    "depenses",
    16,
    Y0,
    616,
    H - Y0 - 16,
    col("Dim_Pays", "Pays"),
    "Dépenses publiques (% PIB)",
    "Dépenses publiques, en % de la richesse produite",
)
b2 = barres(
    p6,
    "prelevements",
    648,
    Y0,
    L - 648 - 16,
    330,
    col("Dim_Pays", "Pays"),
    "Taux de prélèvements obligatoires",
    "Impôts et cotisations, en % de la richesse produite",
    couleur_barres="#2E75B6",
)
p6.sans_filtre(s["pays"], [b1, b2])
phrase(p6, "phrase", 648, Y0 + 342, L - 648 - 16, 120, "Phrase : comparaison")
comprendre(
    p6,
    648,
    Y0 + 470,
    L - 648 - 16,
    H - Y0 - 470 - 16,
    [
        "Rapporter les montants à la richesse produite neutralise la taille des pays. Les écarts tiennent aussi "
        "à l'organisation : dans certains pays, une partie des retraites ou de la santé passe par des organismes "
        "privés obligatoires, qui ne sont pas comptés ici.",
    ],
)


# --- Laboratoire : curseurs ------------------------------------------------------------------
def curseur(page, cle, x, y, w, h, table, colonne, titre):
    return page.ajouter(
        cle,
        "slicer",
        x,
        y,
        w,
        h,
        roles={"Values": [col(table, colonne)]},
        objets={
            "data": [{"properties": {"mode": lit("Single")}}],
            "header": [{"properties": {"show": lit(True), "text": lit(titre)}}],
        },
    )


# --- Page 11 : Projeter la dette --------------------------------------------------------------
pj = Page(
    ident("page", "projeter"), "11. Projeter la dette", "Que deviendrait la dette dans 10 ans ?"
)
en_tete(pj, annee=False)
for i, (t, c, titre) in enumerate(
    [
        (
            "Param Croissance",
            "Croissance réelle (% par an)",
            "Croissance hors inflation (% par an)",
        ),
        ("Param Inflation", "Inflation (% par an)", "Inflation (% par an)"),
        ("Param Ecart Taux", "Écart de taux (points)", "Taux payé : écart au taux actuel (points)"),
        (
            "Param Effort",
            "Effort sur le solde hors intérêts (points de PIB)",
            "Effort sur le solde hors intérêts (points)",
        ),
    ]
):
    curseur(pj, f"curseur{i}", 16, Y0 + i * 104, 300, 96, t, c, titre)
comprendre(
    pj,
    16,
    Y0 + 416,
    300,
    H - Y0 - 416 - 16,
    [
        "Curseurs à 0 : situation de la dernière année connue. Valeurs en % de la richesse produite.",
        "Calcul mécanique, sans effet en retour sur l'économie.",
    ],
)
pj.ajouter(
    "trajectoire",
    "lineChart",
    332,
    Y0,
    L - 332 - 16,
    320,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Y": [
            mes("Dette publique (% PIB)", nom="Dette observée"),
            mes("Dette projetée (% PIB)", nom="Dette projetée"),
        ],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel(
        "Dette publique en % de la richesse produite : observée, puis projetée sur 10 ans"
    ),
)
cw3 = (L - 332 - 16 - 2 * 16) / 3
for i, (m, t) in enumerate(
    [
        ("Dette dans 10 ans (% PIB)", "Dette dans 10 ans"),
        ("Solde hors intérêts qui stabilise la dette (% PIB)", "Solde qui stabilise la dette"),
        ("Intérêts dans 10 ans (% PIB)", "Intérêts de la dette dans 10 ans"),
    ]
):
    carte(pj, f"carte{i}", 332 + i * (cw3 + 16), Y0 + 332, cw3, 88, m, t, taille=22)
phrase(pj, "phrase", 332, Y0 + 432, L - 332 - 16, H - Y0 - 432 - 16, "Phrase : projection")

# --- Page 12 : Et si… ? -----------------------------------------------------------------------
pe = Page(
    ident("page", "et_si"), "12. Et si… ?", "Que changerait une mesure sur le budget de l'année ?"
)
s = en_tete(pe)
pe.ajouter(
    "domaine",
    "slicer",
    16,
    Y0,
    300,
    64,
    roles={"Values": [col("Choix Domaine", "Domaine")]},
    objets={
        "data": [{"properties": {"mode": lit("Dropdown")}}],
        "selection": [{"properties": {"strictSingleSelect": lit(True), "singleSelect": lit(True)}}],
        "header": [
            {"properties": {"show": lit(True), "text": lit("Domaine de dépense (vide = tous)")}}
        ],
    },
)
for i, (t, c, titre) in enumerate(
    [
        (
            "Param Depense Domaine",
            "Variation des dépenses du domaine (%)",
            "Dépenses du domaine (%)",
        ),
        ("Param Salaires", "Variation des salaires publics (%)", "Salaires des agents publics (%)"),
        ("Param Prestations", "Variation des prestations sociales (%)", "Prestations sociales (%)"),
        (
            "Param TVA",
            "Hausse des taux de TVA (%)",
            "Taux de taxe sur la valeur ajoutée (% de hausse)",
        ),
    ]
):
    curseur(pe, f"curseur{i}", 16, Y0 + 72 + i * 104, 300, 96, t, c, titre)
comprendre(
    pe,
    332,
    Y0 + 460,
    L - 332 - 16,
    H - Y0 - 460 - 16,
    [
        "Effet mécanique sur une année, sans changement de comportement. Les leviers peuvent se recouper : "
        "les salaires d'un domaine sont aussi des dépenses de ce domaine.",
        "Taxe sur la valeur ajoutée : tous les taux varient dans la même proportion (20 % → 21 % = +5 %).",
    ],
)
pe.ajouter(
    "effets",
    "clusteredColumnChart",
    332,
    Y0,
    L - 332 - 16,
    240,
    roles={
        "Y": [
            mes("Effet dépenses du domaine (Md€)", nom="Dépenses du domaine"),
            mes("Effet salaires publics (Md€)", nom="Salaires publics"),
            mes("Effet prestations (Md€)", nom="Prestations sociales"),
            mes("Effet TVA (Md€)", nom="Taxe sur la valeur ajoutée"),
        ]
    },
    objets={
        "labels": [{"properties": {"show": lit(True)}}],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel(
        "Effet de chaque mesure sur le solde (en milliards d'euros ; positif : le déficit baisse)"
    ),
)
cw4 = (L - 332 - 16 - 3 * 16) / 4
for i, (m, t) in enumerate(
    [
        ("Solde public (% PIB)", "Solde de l'année, avant"),
        ("Solde simulé (% PIB)", "Solde de l'année, après"),
        ("Effet total sur le solde (Md€)", "Effet total"),
        ("Effet total par habitant (€)", "Effet total par habitant"),
    ]
):
    carte(pe, f"carte{i}", 332 + i * (cw4 + 16), Y0 + 252, cw4, 88, m, t, taille=22)
phrase(pe, "phrase", 332, Y0 + 352, L - 332 - 16, 100, "Phrase : simulation")

# --- Prévisions : couleurs du graphique en spaghetti ------------------------------------------
import duckdb as _duckdb  # noqa: E402

EDITIONS = _duckdb.sql(
    "select institution, libelle from '" + str(RACINE / "data/curated") + "/"
    "dim_edition_prevision.parquet' order by ordre_tri"
).fetchall()
COULEUR_INSTITUTION = {
    "Commission européenne": "#9DB3C8",
    "FMI": "#E3A86B",
    "Gouvernement": "#C0504D",
    "Réalité": "#000000",
}


def selecteur_edition(libelle):
    return {
        "data": [
            {
                "scopeId": {
                    "Comparison": {
                        "ComparisonKind": 0,
                        "Left": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": "Dim_Edition_Prevision"}},
                                "Property": "Édition",
                            }
                        },
                        "Right": {"Literal": {"Value": "'" + libelle.replace("'", "''") + "'"}},
                    }
                }
            }
        ]
    }


def segment_simple(page, cle, x, y, w, h, colonne_f, titre, defaut=None, unique=True):
    objets = {
        "data": [{"properties": {"mode": lit("Dropdown")}}],
        "header": [{"properties": {"show": lit(True), "text": lit(titre)}}],
    }
    if unique:
        objets["selection"] = [
            {
                "properties": {
                    "strictSingleSelect": lit(True),
                    "singleSelect": lit(True),
                    "selectAllCheckboxEnabled": lit(False),
                }
            }
        ]
    if defaut:
        objets["general"] = [{"properties": {"filter": {"filter": filtre(colonne_f, [defaut])}}}]
    return page.ajouter(cle, "slicer", x, y, w, h, roles={"Values": [colonne_f]}, objets=objets)


VARIABLE = col("Dim_Variable_Prevision", "Indicateur prévu")
INSTITUTION = col("Dim_Edition_Prevision", "Institution")

# --- Page 13 : Mes scénarios ---------------------------------------------------------------------
SCENARIOS = [
    libelle
    for (libelle,) in _duckdb.sql(
        "select libelle from '"
        + str(RACINE / "data/curated")
        + "/dim_scenario.parquet' order by ordre_tri"
    ).fetchall()
]
ps = Page(ident("page", "scenarios"), "13. Mes scénarios", "Où mènent les différents scénarios ?")
s = en_tete(ps, annee=False)
ps.ajouter(
    "choix",
    "slicer",
    16,
    Y0,
    300,
    330,
    roles={"Values": [col("Dim_Scenario", "Scénario")]},
    objets={
        "data": [{"properties": {"mode": lit("Basic")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit(False)}}],
        "general": [
            {
                "properties": {
                    "filter": {"filter": filtre(col("Dim_Scenario", "Scénario"), SCENARIOS[:4])}
                }
            }
        ],
        "header": [{"properties": {"show": lit(True), "text": lit("Scénarios à comparer")}}],
    },
)
comprendre(
    ps,
    16,
    Y0 + 342,
    300,
    H - Y0 - 342 - 16,
    [
        "Chaque scénario est un fichier du dossier « scenarios » du dépôt, recalculé à chaque mise à jour.",
        "Les emprunts qui arrivent à échéance sont renouvelés au taux du marché : une hausse des taux ne pèse "
        "que progressivement sur le taux moyen payé.",
    ],
)
AXE_S = {
    "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}],
    "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
    "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
}
ps.ajouter(
    "dette",
    "lineChart",
    332,
    Y0,
    L - 332 - 16,
    300,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Series": [col("Dim_Scenario", "Scénario")],
        "Y": [mes("Dette selon le scénario (% PIB)", nom="Dette")],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets=AXE_S,
    conteneur=titre_visuel("Dette publique selon le scénario, en % de la richesse produite"),
)
phrase(ps, "phrase", 332, Y0 + 312, L - 332 - 16, 96, "Phrase : scénarios")
ps.ajouter(
    "taux",
    "lineChart",
    332,
    Y0 + 420,
    460,
    H - Y0 - 420 - 16,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Series": [col("Dim_Scenario", "Scénario")],
        "Y": [mes("Taux moyen payé selon le scénario", nom="Taux moyen")],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={**AXE_S, "legend": [{"properties": {"show": lit(False)}}]},
    conteneur=titre_visuel("Taux moyen payé sur la dette"),
)
ps.ajouter(
    "tableau",
    "tableEx",
    808,
    Y0 + 420,
    L - 808 - 16,
    H - Y0 - 420 - 16,
    roles={
        "Values": [
            col("Dim_Scenario", "Scénario"),
            mes("Année de fin du scénario", nom="Jusqu'en"),
            mes("Dette en fin de scénario (% PIB)", nom="Dette"),
            mes("Intérêts en fin de scénario (% PIB)", nom="Intérêts"),
        ]
    },
    objets={
        "values": [{"properties": {"wordWrap": lit(True)}}],
        "columnHeaders": [{"properties": {"wordWrap": lit(True)}}],
    },
    conteneur=titre_visuel("À l'horizon de chaque scénario (en % de la richesse produite)"),
)

# --- Page 14 : Prévisions et réalité ---------------------------------------------------------
pv = Page(
    ident("page", "previsions"),
    "14. Prévisions et réalité",
    "Les prévisions annoncées se sont-elles réalisées ?",
)
s = en_tete(pv, annee=False)
segment_simple(
    pv, "variable", 16, Y0, 400, 62, VARIABLE, "Indicateur", defaut="Dette publique (% du PIB)"
)
segment_simple(
    pv, "institution", 432, Y0, 400, 62, INSTITUTION, "Institution (vide = toutes)", unique=False
)
couleurs = [
    {"properties": {"fill": couleur(COULEUR_INSTITUTION[inst])}, "selector": selecteur_edition(lib)}
    for inst, lib in EDITIONS
]
epaisseurs = [{"properties": {"strokeWidth": lit(1.0)}}] + [
    {"properties": {"strokeWidth": lit(4.0)}, "selector": selecteur_edition(lib)}
    for inst, lib in EDITIONS
    if inst == "Réalité"
]
pv.ajouter(
    "spaghetti",
    "lineChart",
    16,
    Y0 + 74,
    L - 32,
    380,
    roles={
        "Category": [col("Dim_Date", "Année")],
        "Series": [col("Dim_Edition_Prevision", "Édition")],
        "Y": [mes("Valeur prévue", nom="Valeur")],
    },
    tri=(col("Dim_Date", "Année"), "Ascending"),
    objets={
        "categoryAxis": [
            {"properties": {"showAxisTitle": lit(False), "axisType": lit("Categorical")}}
        ],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(False)}}],
        "dataPoint": couleurs,
        "lineStyles": epaisseurs,
    },
    conteneur=titre_visuel(
        "Chaque ligne fine est une prévision publiée ; la ligne noire épaisse, ce qui s'est passé"
    ),
)
phrase(pv, "phrase", 16, Y0 + 466, 820, H - Y0 - 466 - 16, "Phrase : dernière prévision")
comprendre(
    pv,
    852,
    Y0 + 466,
    L - 852 - 16,
    H - Y0 - 466 - 16,
    [
        "En bleu : la Commission européenne (deux fois par an depuis 2011). En rouge : le gouvernement. "
        "En orange : le FMI, dont seule l'édition en cours est accessible.",
    ],
    source="Sources : Commission européenne (AMECO), FMI, Eurostat.",
)

# --- Page 15 : Qui se trompe ? ----------------------------------------------------------------
pb = Page(
    ident("page", "biais"), "15. Qui se trompe ?", "Les prévisions sont-elles trop optimistes ?"
)
s = en_tete(pb, annee=False)
segment_simple(
    pb, "variable", 16, Y0, 300, 62, VARIABLE, "Indicateur", defaut="Solde public (% du PIB)"
)
segment_simple(
    pb, "institution", 332, Y0, 300, 62, INSTITUTION, "Institution (vide = toutes)", unique=False
)
horizons = filtre_visuel(
    ident(pb.nom, "f_horizon"), col("Fait_Previsions", "Horizon (années)"), [0, 1, 2]
)
pb.ajouter(
    "horizons",
    "clusteredColumnChart",
    16,
    Y0 + 74,
    616,
    250,
    roles={
        "Category": [col("Fait_Previsions", "Horizon")],
        "Series": [INSTITUTION],
        "Y": [mes("Biais d'optimisme (points)", nom="Biais")],
    },
    tri=(col("Fait_Previsions", "Horizon"), "Ascending"),
    objets={
        "labels": [{"properties": {"show": lit(True)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
    },
    conteneur=titre_visuel("Biais moyen selon l'horizon (en points ; positif : trop optimiste)"),
    filtres=[horizons],
)
cw3p = (616 - 32) / 3
for i, (m, t) in enumerate(
    [
        ("Biais d'optimisme à un an (points)", "Biais à un an"),
        ("Erreur absolue moyenne à un an (points)", "Erreur moyenne à un an"),
        ("Prévisions comparées à un an", "Prévisions comparées"),
    ]
):
    carte(pb, f"carte{i}", 16 + i * (cw3p + 16), Y0 + 336, cw3p, 88, m, t, taille=22)
phrase(pb, "phrase", 16, Y0 + 436, 616, 144, "Phrase : biais des prévisions")
comprendre(
    pb,
    16,
    Y0 + 588,
    616,
    H - Y0 - 588 - 16,
    [
        "Biais positif : la prévision annonçait mieux que la réalité (déficit plus faible, dette plus basse).",
    ],
)
bp = barres(
    pb,
    "pays",
    648,
    Y0 + 74,
    L - 648 - 16,
    H - Y0 - 74 - 16,
    col("Dim_Pays", "Pays"),
    "Biais d'optimisme à un an (points)",
    "Biais des prévisions à un an, par pays (en points)",
)
pb.sans_filtre(s["pays"], [bp])

# --- Page 16 : Glossaire -----------------------------------------------------------------------
p7 = Page(ident("page", "glossaire"), "16. Glossaire", "Que veulent dire ces mots ?")
p7.ajouter("navigation", "pageNavigator", 16, 8, L - 32, 40, conteneur=sans_titre())
texte(
    p7,
    "titre",
    16,
    54,
    820,
    62,
    [[(p7.question, {"gras": True, "taille": "20pt", "couleur": BLEU})]],
)
p7.ajouter(
    "segment_terme",
    "slicer",
    L - 16 - 320,
    54,
    320,
    62,
    roles={"Values": [col("Dim_Glossaire", "Terme")]},
    objets={
        "data": [{"properties": {"mode": lit("Dropdown")}}],
        "general": [{"properties": {"selfFilterEnabled": lit(True)}}],
        "header": [{"properties": {"show": lit(True), "text": lit("Chercher un terme")}}],
    },
)
p7.ajouter(
    "table",
    "tableEx",
    16,
    Y0,
    L - 32,
    H - Y0 - 16,
    roles={
        "Values": [
            col("Dim_Glossaire", "Terme"),
            col("Dim_Glossaire", "En bref"),
            col("Dim_Glossaire", "Pour aller plus loin"),
        ]
    },
    tri=(col("Dim_Glossaire", "Terme"), "Ascending"),
    objets={
        "values": [{"properties": {"wordWrap": lit(True)}}],
        "columnHeaders": [{"properties": {"wordWrap": lit(True)}}],
        "columnWidth": [
            {"properties": {"value": lit(220.0)}, "selector": {"metadata": "Dim_Glossaire.Terme"}},
            {
                "properties": {"value": lit(420.0)},
                "selector": {"metadata": "Dim_Glossaire.En bref"},
            },
            {
                "properties": {"value": lit(560.0)},
                "selector": {"metadata": "Dim_Glossaire.Pour aller plus loin"},
            },
        ],
    },
    conteneur=sans_titre(),
)

if TROP_PETITES:
    raise SystemExit("Cartes trop petites :\n" + "\n".join(map(str, TROP_PETITES)))

# --- Finition : sommaire de l'accueil ----------------------------------------------------------
pages = [p1, p2, p3, p4, p5, pd, pq, pt, pr, p6, pj, pe, ps, pv, pb, p7]
largeur_bouton = (L - 32 - 2 * 12) / 3
for i, cible in enumerate(pages[1:]):
    colonne, ligne = i % 3, i // 3
    p1.ajouter(
        f"bouton{i}",
        "actionButton",
        16 + colonne * (largeur_bouton + 12),
        Y0 + 344 + ligne * 46,
        largeur_bouton,
        42,
        objets={
            # « show » est une propriété commune à tous les états du bouton : sans sélecteur.
            # Les propriétés propres à un état (texte, couleurs) portent le sélecteur « default ».
            "icon": [{"properties": {"show": lit(False)}}],
            "text": [
                {"properties": {"show": lit(True)}},
                {
                    "properties": {
                        "text": lit(f"{cible.titre} — {cible.question}"),
                        "fontSize": lit(10.0),
                        "fontColor": couleur(BLEU),
                        "horizontalAlignment": lit("left"),
                    },
                    "selector": {"id": "default"},
                },
            ],
            "fill": [
                {"properties": {"show": lit(True)}},
                {"properties": {"fillColor": couleur(FOND_ENCADRE)}, "selector": {"id": "default"}},
            ],
        },
        conteneur={
            "visualLink": [
                {
                    "properties": {
                        "show": lit(True),
                        "type": lit("PageNavigation"),
                        "navigationSection": lit(cible.nom),
                    }
                }
            ]
        },
    )

# --- Finition : info-bulles de définition (glossaire) -----------------------------------------
import csv as _csv  # noqa: E402

with open(RACINE / "data/reference/ref_glossaire.csv", encoding="utf-8") as _f:
    GLOSSAIRE = {r["terme"]: r for r in _csv.DictReader(_f)}
INFOBULLES = [
    (p1, "carte0", "Dépenses publiques"),
    (p1, "carte1", "Recettes publiques"),
    (p1, "carte2", "Déficit public (besoin de financement)"),
    (p2, "pour100", "PIB (produit intérieur brut)"),
    (p2, "taux_po", "Prélèvements obligatoires"),
    (p2, "solde", "Déficit public (besoin de financement)"),
    (p3, "legal", "Lecture légale et lecture économique"),
    (p3, "eco", "Lecture légale et lecture économique"),
    (p3, "assiette", "Prélèvements obligatoires"),
    (p4, "fonctions", "Fonction (à quoi sert l'argent)"),
    (p5, "transferts", "Consolidation"),
    (pd, "carte0", "Dette publique (au sens de Maastricht)"),
    (pd, "carte3", "Taux moyen payé sur la dette (taux apparent)"),
    (pd, "decomposition", "Effet boule de neige"),
    (pq, "detenteurs", "Détenteurs de la dette"),
    (pq, "taux", "Taux d'emprunt à 10 ans"),
    (pt, "solde", "Correction des variations saisonnières"),
    (pr, "ecart", "Écart de taux avec l'Allemagne"),
    (pr, "courbe", "Courbe des taux"),
    (pr, "indexee", "Dette indexée sur l'inflation"),
    (pj, "trajectoire", "Projection mécanique"),
    (pj, "carte1", "Solde hors intérêts (solde primaire)"),
    (ps, "dette", "Scénario tendanciel"),
    (ps, "taux", "Refinancement de la dette"),
    (pb, "horizons", "Biais d'optimisme"),
]
pages_infobulles = {}
for _, _, terme in INFOBULLES:
    if terme in pages_infobulles:
        continue
    g = GLOSSAIRE[terme]
    pi = Page(
        ident("infobulle", terme),
        f"Définition : {terme}"[:48],
        terme,
        infobulle=True,
        largeur=360,
        hauteur=240,
    )
    texte(
        pi,
        "definition",
        0,
        0,
        360,
        240,
        [
            [(terme, {"gras": True, "taille": "12pt", "couleur": BLEU})],
            [(g["definition_courte"][0].upper() + g["definition_courte"][1:], {"taille": "11pt"})],
            [("Plus de détails : page Glossaire.", {"taille": "9pt"})],
        ],
        FOND_ENCADRE,
    )
    pages_infobulles[terme] = pi
for page, cle, terme in INFOBULLES:
    v = page.visuel(cle)
    v["visual"].setdefault("visualContainerObjects", {})["visualTooltip"] = [
        {
            "properties": {
                "show": lit(True),
                "type": lit("Canvas"),
                "section": lit(pages_infobulles[terme].nom),
            }
        }
    ]

# --- Finition : repères des crises sur les courbes annuelles -----------------------------------
for page, cle in [(p2, "courbes"), (pd, "ratio")]:
    q = page.visuel(cle)["visual"]["query"]["queryState"]
    q["Tooltips"] = {"projections": [projection(mes("Repère historique", nom="Période"))]}

pages = pages + list(pages_infobulles.values())

# --- Écriture ---------------------------------------------------------------------------------
for p in pages:
    dossier = PAGES / p.nom
    if (dossier / "visuals").exists():
        shutil.rmtree(dossier / "visuals")  # dossiers générés par ce script uniquement
    (dossier / "visuals").mkdir(parents=True, exist_ok=True)
    doc = {
        "$schema": P_SCHEMA,
        "name": p.nom,
        "displayName": p.titre,
        "displayOption": "FitToPage",
        "height": p.hauteur,
        "width": p.largeur,
    }
    if p.infobulle:
        doc["pageBinding"] = {"name": ident("liaison", p.nom), "type": "Tooltip"}
        doc["type"] = "Tooltip"
        doc["visibility"] = "HiddenInViewMode"
    if p.interactions:
        doc["visualInteractions"] = p.interactions
    (dossier / "page.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for v in p.visuels:
        d = dossier / "visuals" / v["name"]
        d.mkdir()
        (d / "visual.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

meta = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
meta["pageOrder"] = [p.nom for p in pages]
meta["activePageName"] = p1.nom
(PAGES / "pages.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"{len(pages)} pages, {sum(len(p.visuels) for p in pages)} visuels")
