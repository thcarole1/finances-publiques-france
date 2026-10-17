"""Contrôles syntaxiques légers des fichiers TMDL du modèle Power BI.

Ils ne remplacent pas l'ouverture dans Power BI Desktop, mais attrapent les erreurs
d'écriture les plus courantes avant qu'elles n'arrivent dans Desktop.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
FICHIERS = sorted((RACINE / "powerbi").rglob("*.tmdl"))

# Lignes qui déclarent un objet nommé ou référencent une colonne par son nom.
DECLARATION = re.compile(
    r"^\t*(table|column|measure|hierarchy|level|partition|expression|ref table)\s+(?P<nom>.+?)"
    r"(\s*=.*)?$"
)
REFERENCE = re.compile(r"^\t*(sortByColumn|column):\s*(?P<nom>.+)$")


def _nom_valide(nom: str) -> bool:
    """Un nom TMDL est soit simple (lettres, chiffres, _), soit entre apostrophes avec les
    apostrophes internes doublées."""
    nom = nom.strip()
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nom):
        return True
    if len(nom) >= 2 and nom[0] == nom[-1] == "'":
        interieur = nom[1:-1]
        return "'" not in interieur.replace("''", "")
    return False


@pytest.mark.parametrize("fichier", FICHIERS, ids=lambda f: f.name)
def test_noms_tmdl_correctement_cites(fichier):
    erreurs = []
    for num, ligne in enumerate(fichier.read_text(encoding="utf-8").splitlines(), 1):
        if ligne.lstrip().startswith(("///", "annotation", "source", "lineageTag")):
            continue
        m = DECLARATION.match(ligne) or REFERENCE.match(ligne)
        if m and not _nom_valide(m.group("nom")):
            erreurs.append(f"ligne {num} : {ligne.strip()}")
    assert not erreurs, "Noms TMDL mal cités :\n" + "\n".join(erreurs)


def test_regle_de_citation():
    assert _nom_valide("Dim_Date")
    assert _nom_valide("'Année'")
    assert _nom_valide("'Est fin d''année'")
    assert not _nom_valide("'Est fin d'année'")
    assert not _nom_valide("Année")
