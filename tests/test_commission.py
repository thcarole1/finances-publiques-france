"""Connecteur AMECO : repérage de l'édition en ligne."""

import pytest

from ingestion.sources.commission import edition_courante, saison_du_mois

LIEN = (
    '<a href="/document/download/abc_en" class="ecl-link" '
    'data-untranslated-label="AMECO - All zipped TXT files" id="x">'
)


def test_mention_last_update():
    page = f"<p>Last update: 15 May 2025 - Spring 2025</p>{LIEN}"
    e = edition_courante(page)
    assert e.identifiant == "2025-printemps"
    assert e.url.endswith("/document/download/abc_en")


def test_date_du_fichier_sans_mention():
    # Présentation de la page depuis novembre 2026 : seule la date du fichier est affichée.
    page = (
        '<div class="ecl-file__title">AMECO - All zipped TXT files</div>'
        '<div class="ecl-file__primary-meta"><div class="ecl-file__primary-meta-item">'
        f"17 November 2026</div></div>{LIEN}"
    )
    assert edition_courante(page).identifiant == "2026-automne"


@pytest.mark.parametrize(("mois", "saison"), [(2, "hiver"), (5, "printemps"), (11, "automne")])
def test_saison_du_mois(mois, saison):
    assert saison_du_mois(mois) == saison


def test_page_illisible():
    with pytest.raises(RuntimeError):
        edition_courante("<p>rien</p>")
