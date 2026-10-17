"""Connecteur BCE (Banque centrale européenne) : portail de données, API SDMX publique.

Usage :
    uv run python -m ingestion.sources.bce

Jeu collecté : courbe des taux de la zone euro (flux YC), taux au comptant à 1, 2, 5, 10, 20
et 30 ans, pour les emprunts d'État notés AAA et pour l'ensemble des emprunts d'État de la zone
euro. Données quotidiennes depuis septembre 2004, téléchargées **sans transformation** (CSV,
compressé en gzip) dans ``data/raw/bce/<jeu>/<date_collecte>/``.
"""

from __future__ import annotations

import argparse
import gzip
import sys
from datetime import date
from pathlib import Path

from ingestion.common.archivage import RACINE_RAW, Instantane, dossier_instantane
from ingestion.common.http import creer_session

SOURCE = "bce"
JEU = "courbe-taux"
MATURITES = [1, 2, 5, 10, 20, 30]
URL = "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM." + "+".join(
    f"SR_{m}Y" for m in MATURITES
)
PARAMETRES = {"format": "csvdata", "detail": "dataonly", "startPeriod": "2004-09-01"}


def collecter(date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path:
    session = creer_session()
    r = session.get(URL, params=PARAMETRES, timeout=600)
    r.raise_for_status()
    if not r.content.startswith(b"KEY,"):
        raise RuntimeError(f"Réponse BCE inattendue : {r.content[:300]!r}")
    print(f"  {JEU} : {len(r.content):,} octets", file=sys.stderr)
    with Instantane(SOURCE, JEU, date_collecte, None, racine) as inst:
        inst.ajouter(
            "donnees.csv.gz", gzip.compress(r.content, mtime=0), url=r.url, parametres=PARAMETRES
        )
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ignorer-existants", action="store_true")
    args = parser.parse_args(argv)
    if args.ignorer_existants and dossier_instantane(SOURCE, JEU, date.today()).exists():
        print("Collecte BCE : déjà collectée aujourd'hui, ignorée", file=sys.stderr)
        return 0
    print("Collecte BCE : courbe des taux de la zone euro", file=sys.stderr)
    print(f"  → {collecter()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
