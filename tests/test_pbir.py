"""Cohérence entre le rapport (PBIR) et le modèle (TMDL).

Chaque champ utilisé par un visuel ou un filtre du rapport doit exister dans le modèle, avec la
bonne nature (colonne ou mesure). Sinon, Power BI Desktop affiche le visuel en erreur
(« Un ou plusieurs champs sont introuvables »).
"""

import json
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "powerbi/FinancesPubliques.SemanticModel/definition/tables"
RAPPORT = RACINE / "powerbi/FinancesPubliques.Report/definition"

DECL = re.compile(r"^\t(column|measure)\s+(?P<nom>'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_]*)")


def _nom(brut: str) -> str:
    return brut[1:-1].replace("''", "'") if brut.startswith("'") else brut


def objets_du_modele() -> set[tuple[str, str, str]]:
    objets = set()
    for f in MODELE.glob("*.tmdl"):
        texte = f.read_text(encoding="utf-8")
        table = _nom(re.search(r"^table\s+(.+)$", texte, re.M).group(1).strip())
        for ligne in texte.splitlines():
            m = DECL.match(ligne)
            if m:
                nature = "Column" if m.group(1) == "column" else "Measure"
                objets.add((table, nature, _nom(m.group("nom"))))
    return objets


def references(noeud, alias=None):
    """Parcourt un document PBIR et rend les (entité, nature, propriété) référencés."""
    alias = dict(alias or {})
    if isinstance(noeud, dict):
        for source in noeud.get("From", []):
            alias[source["Name"]] = source["Entity"]
        for nature in ("Column", "Measure"):
            ref = noeud.get(nature)
            if isinstance(ref, dict) and "Property" in ref:
                src = ref["Expression"]["SourceRef"]
                entite = src.get("Entity") or alias.get(src.get("Source"))
                yield entite, nature, ref["Property"]
        for v in noeud.values():
            yield from references(v, alias)
    elif isinstance(noeud, list):
        for v in noeud:
            yield from references(v, alias)


FICHIERS = sorted(RAPPORT.rglob("visual.json")) + sorted(RAPPORT.rglob("page.json"))


def test_le_rapport_a_des_visuels():
    assert len(list(RAPPORT.rglob("visual.json"))) > 0


def _id(f: Path) -> str:
    return f"{f.parent.parent.parent.name}/{f.parent.name}"


@pytest.mark.parametrize("fichier", FICHIERS, ids=_id)
def test_champs_existent_dans_le_modele(fichier):
    modele = objets_du_modele()
    doc = json.loads(fichier.read_text(encoding="utf-8"))
    manquants = sorted({r for r in references(doc) if r not in modele})
    assert not manquants, f"Champs absents du modèle : {manquants}"


SIGLES_INTERDITS = re.compile(r"\b(APU|APUL|ODAC|ASSO|COFOG|SEC|S13\w*|D\d{2,3}\w*|n\.c\.a\.)\b")


@pytest.mark.parametrize("fichier", sorted(RAPPORT.rglob("visual.json")), ids=_id)
def test_aucun_sigle_dans_les_textes_affiches(fichier):
    """Règle du rapport (docs/09, § 6) : pas de sigle ni de code technique dans un visuel.

    Seules les sources citées en pied d'encadré peuvent nommer une nomenclature."""
    doc = json.loads(fichier.read_text(encoding="utf-8"))
    textes = []

    def collecter(n):
        if isinstance(n, dict):
            for k, v in n.items():
                affiche = k in ("value", "text", "displayName") or (
                    k == "Value" and str(v).startswith("'")
                )
                if affiche and isinstance(v, str):
                    textes.append(v)
                else:
                    collecter(v)
        elif isinstance(n, list):
            for v in n:
                collecter(v)

    collecter(doc.get("visual", {}).get("objects", {}))
    collecter(doc.get("visual", {}).get("visualContainerObjects", {}))
    fautifs = [t for t in textes if SIGLES_INTERDITS.search(t) and not t.startswith("Source")]
    assert not fautifs, f"Sigles ou codes dans un texte affiché : {fautifs}"


def test_boutons_affichent_leur_texte():
    """Bouton : « show » doit être hors sélecteur d'état, sinon le texte reste invisible."""
    boutons = 0
    for f in RAPPORT.glob("pages/*/visuals/*/visual.json"):
        v = json.loads(f.read_text(encoding="utf-8"))["visual"]
        if v["visualType"] != "actionButton":
            continue
        boutons += 1
        texte = v["objects"]["text"]
        assert any("selector" not in e and "show" in e["properties"] for e in texte), f
        assert any("text" in e["properties"] for e in texte), f
    assert boutons >= 15


def test_theme_sans_police_imposee():
    """Le thème ne change pas les polices : les cartes et étiquettes sont dimensionnées pour
    les polices par défaut (une autre police coupe les chiffres en haut et en bas)."""
    theme = json.loads(
        (
            RACINE / "powerbi/FinancesPubliques.Report/StaticResources/RegisteredResources/"
            "FinancesPubliques.json"
        ).read_text(encoding="utf-8")
    )
    assert "textClasses" not in theme
