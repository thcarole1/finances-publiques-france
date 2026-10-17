"""Tests du connecteur Eurostat (sans accès réseau)."""

from types import SimpleNamespace

from ingestion.sources.eurostat import geos_refuses

ERREUR = (
    "<S:Fault><faultcode>150</faultcode><faultstring>INVALID_QUERY_DIMENSION_VALUE: Query is "
    "invalid as per its structure&apos;s definition. The following values for dimension are not "
    "allowed: GEO=CH, GEO=NO.</faultstring></S:Fault>"
)


def test_pays_refuses_extraits_de_l_erreur():
    assert geos_refuses(SimpleNamespace(status_code=400, text=ERREUR)) == ["CH", "NO"]


def test_aucun_pays_refuse_si_reponse_valide():
    assert geos_refuses(SimpleNamespace(status_code=200, text="GEO=FR")) == []
