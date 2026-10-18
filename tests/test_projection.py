"""Tests du moteur de projection (projection/)."""

import pandas as pd
import pytest

from projection.moteur import Depart, Emission, Hypotheses, appliquer_surcharges, projeter
from projection.scenarios import hypotheses_gouvernement, hypotheses_tendancielles

DEPART = Depart(
    annee=2025,
    dette_meur=3460.0,
    pib_meur=2991.0,
    taux_apparent=2.0,
    solde_primaire_pib=-2.9,
    taux_10_ans=3.4,
)


def test_controle_croise_avec_la_formule_fermee_du_laboratoire():
    """Taux apparent et croissance constants : même résultat que la mesure DAX du laboratoire."""
    hyp = Hypotheses(
        {
            "croissance_volume": {2026: 1.0},
            "inflation": {2026: 1.8},
            "taux_apparent": {2026: 2.0},
            "solde_primaire": {2026: -2.9},
        }
    )
    fin = projeter(DEPART, hyp, 2035, Emission())[-1]
    i, g = 0.02, 1.01 * 1.018 - 1
    f, d0, sp = (1 + i) / (1 + g), 3460 / 2991, -0.029
    assert fin.dette_pib == pytest.approx(100 * (d0 * f**10 - sp * (f**10 - 1) / (f - 1)), abs=1e-9)


def test_une_hausse_des_taux_se_transmet_lentement():
    hyp = hypotheses_tendancielles(DEPART)
    hyp.valeurs["taux_10_ans"] = {2026: 5.0}
    res = projeter(DEPART, hyp, 2040, Emission(duree_vie_stock=8))
    apparents = [r.taux_apparent for r in res]
    assert apparents[0] == pytest.approx(2.0)  # 1re année : intérêts sur la dette déjà émise
    assert all(
        b >= a - 1e-9 for a, b in zip(apparents, apparents[1:], strict=False)
    )  # hausse progressive
    assert apparents[3] < 4.0 < apparents[-1] <= 5.0 + 1e-9  # loin du taux de marché au début


def test_la_trajectoire_du_gouvernement_atteint_ses_cibles_de_solde():
    traj = pd.DataFrame(
        [("SOLDE", 2026, -5.4), ("SOLDE", 2027, -5.0), ("CROISSANCE", 2026, 0.5)],
        columns=["variable_code", "annee", "valeur"],
    )
    res = projeter(DEPART, hypotheses_gouvernement(DEPART, traj), 2030, Emission())
    assert res[0].solde_pib == pytest.approx(-5.4)
    assert res[1].solde_pib == pytest.approx(-5.0)
    assert res[0].croissance_volume == pytest.approx(0.5)
    # Après 2027, le solde hors intérêts reste celui de 2027.
    assert res[3].solde_primaire_pib == pytest.approx(res[1].solde_primaire_pib)


def test_surcharges_ecart_et_valeur():
    base = Hypotheses({"taux_10_ans": {a: 3.0 for a in range(2026, 2031)}})
    hyp = appliquer_surcharges(
        base, {"taux_10_ans": {"ecart": {"2027": 1.5}, "valeur": {"2029": 2.0}}}, 2030
    )
    assert [hyp.valeur("taux_10_ans", a) for a in range(2026, 2031)] == [3.0, 4.5, 3.0, 2.0, 3.0]


def test_identite_de_la_dette():
    res = projeter(DEPART, hypotheses_tendancielles(DEPART), 2030, Emission())
    dette = DEPART.dette_meur
    for r in res:
        assert r.dette_meur == pytest.approx(dette - r.solde_meur)
        assert r.solde_meur == pytest.approx(r.solde_primaire_meur - r.interets_meur)
        dette = r.dette_meur
