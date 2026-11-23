"""Connecteur DG TAXUD : listes nationales des impôts (« National Tax Lists », NTL).

Pour chaque pays de l'UE (+ Islande, Norvège), chaque impôt national est rattaché à son code
SEC 2010 et à sa base économique (consommation, travail, capital…), selon la méthodologie
« Taxation Trends » de la Commission européenne. Le fichier est republié à chaque édition
annuelle, sous une URL qui change : on la retrouve sur la page « Data on Taxation Trends ».

Usage :
    uv run python -m ingestion.sources.taxud
    uv run python -m ingestion.sources.taxud --fichier "NTL edition 2026 web.xlsx" --edition 2026

Le site de la Commission refuse parfois les téléchargements automatiques (erreur 429) : le
fichier, téléchargé à la main depuis la page ci-dessous, s'intègre alors avec --fichier.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from ingestion.common.archivage import RACINE_RAW, Instantane, dossier_instantane
from ingestion.common.http import creer_session

SOURCE = "taxud"
JEU = "ntl"
PAGE = "https://taxation-customs.ec.europa.eu/taxation/economic-analysis/data-taxation-trends_en"
MOTIF_LIEN = re.compile(r'href="(?P<url>[^"]*NTL[^"]*\.xlsx[^"]*)"', re.IGNORECASE)
MOTIF_EDITION = re.compile(r"edition[%20\s_-]*(?P<annee>20\d\d)", re.IGNORECASE)


def trouver_lien(page_html: str) -> tuple[str, str | None]:
    """URL du fichier NTL et année d'édition, à partir de la page de la DG TAXUD."""
    m = MOTIF_LIEN.search(page_html)
    if not m:
        raise RuntimeError(
            "Lien vers les listes nationales des impôts (NTL) introuvable sur la page."
        )
    url = urljoin(PAGE, html.unescape(m["url"]))
    e = MOTIF_EDITION.search(url)
    return url, (e["annee"] if e else None)


def collecter(date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path:
    session = creer_session()
    page = session.get(PAGE, timeout=120)
    page.raise_for_status()
    url, edition = trouver_lien(page.text)
    r = session.get(url, timeout=600)
    r.raise_for_status()
    if r.content[:2] != b"PK":
        raise RuntimeError(f"Le fichier téléchargé n'est pas un classeur Excel : {url}")
    with Instantane(SOURCE, JEU, date_collecte, None, racine) as inst:
        inst.ajouter("ntl.xlsx", r.content, url=url, parametres={"edition": edition})
    return inst.dossier


def integrer_fichier(
    fichier: Path, edition: str | None, date_collecte: date | None = None, racine: Path = RACINE_RAW
) -> Path:
    """Instantané à partir d'un fichier téléchargé à la main."""
    contenu = fichier.read_bytes()
    if contenu[:2] != b"PK":
        raise RuntimeError(f"{fichier} n'est pas un classeur Excel.")
    with Instantane(SOURCE, JEU, date_collecte, None, racine) as inst:
        inst.ajouter(
            "ntl.xlsx",
            contenu,
            url=PAGE,
            parametres={"edition": edition, "telechargement": "manuel"},
        )
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ignorer-existants", action="store_true")
    parser.add_argument("--fichier", type=Path, help="Classeur NTL téléchargé à la main.")
    parser.add_argument("--edition", help="Année d'édition du classeur (avec --fichier).")
    args = parser.parse_args(argv)
    if args.fichier:
        print(f"  → {integrer_fichier(args.fichier, args.edition)}", file=sys.stderr)
        return 0
    if args.ignorer_existants and dossier_instantane(SOURCE, JEU, date.today()).exists():
        print("Collecte DG TAXUD : déjà collectée aujourd'hui, ignorée", file=sys.stderr)
        return 0
    print("Collecte DG TAXUD : listes nationales des impôts", file=sys.stderr)
    print(f"  → {collecter()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
