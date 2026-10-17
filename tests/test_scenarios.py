import shutil
from pathlib import Path

from scripts.valider_scenarios import valider_dossier

RACINE = Path(__file__).resolve().parents[1]


def _dossier(tmp_path, contenu: str | None = None) -> Path:
    shutil.copy(RACINE / "scenarios" / "_schema.json", tmp_path / "_schema.json")
    if contenu is not None:
        (tmp_path / "s.yml").write_text(contenu, encoding="utf-8")
    return tmp_path


BASE = """
id: PERSO_TEST
libelle: Test
auteur: moi
base: GOUV_PLF_2026
horizon: 2030
hypotheses:
  taux_10_ans:
    ecart:
      2027: 1.5
"""


def test_scenarios_du_depot_valides():
    assert valider_dossier(RACINE / "scenarios") == []


def test_scenario_minimal_valide(tmp_path):
    assert valider_dossier(_dossier(tmp_path, BASE)) == []


def test_variable_inconnue_refusee(tmp_path):
    contenu = BASE.replace("taux_10_ans", "taux_magique")
    assert valider_dossier(_dossier(tmp_path, contenu))


def test_annee_au_dela_de_l_horizon_refusee(tmp_path):
    contenu = BASE.replace("2027: 1.5", "2031: 1.5")
    erreurs = valider_dossier(_dossier(tmp_path, contenu))
    assert any("horizon" in e for e in erreurs)


def test_ecart_et_valeur_sur_la_meme_annee_refuses(tmp_path):
    contenu = BASE + "    valeur:\n      2027: 3.0\n"
    erreurs = valider_dossier(_dossier(tmp_path, contenu))
    assert any("à la fois" in e for e in erreurs)


def test_identifiant_sans_prefixe_refuse(tmp_path):
    contenu = BASE.replace("PERSO_TEST", "TEST")
    assert valider_dossier(_dossier(tmp_path, contenu))
