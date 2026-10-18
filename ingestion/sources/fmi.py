"""Connecteur FMI : prévisions des Perspectives de l'économie mondiale (WEO), API DataMapper.

Usage :
    uv run python -m ingestion.sources.fmi

L'API publique ne sert que l'édition **en vigueur** (avril ou octobre). Chaque collecte conserve
l'édition du moment : au fil des collectes, les éditions successives s'accumulent dans les
Releases et alimentent l'analyse des erreurs de prévision. Les éditions plus anciennes ne sont
pas accessibles depuis la session (fichiers du FMI déplacés sur un portail non accessible).

Indicateurs (JSON brut, compressé) :
- GGXWDG_NGDP : dette brute des administrations publiques, en % du PIB ;
- GGXCNL_NGDP : capacité (+) ou besoin (−) de financement, en % du PIB ;
- NGDP_RPCH : croissance du PIB en volume, en %.
"""

from __future__ import annotations

import argparse
import gzip
import sys
from datetime import date
from pathlib import Path

from ingestion.common.archivage import RACINE_RAW, Instantane, dossier_instantane
from ingestion.common.http import creer_session

SOURCE = "fmi"
JEU = "weo"
URL = "https://www.imf.org/external/datamapper/api/v1/{indicateur}"
INDICATEURS = ["GGXWDG_NGDP", "GGXCNL_NGDP", "NGDP_RPCH"]


def collecter(date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path:
    session = creer_session()
    contenus = {}
    for ind in INDICATEURS:
        r = session.get(URL.format(indicateur=ind), timeout=120)
        r.raise_for_status()
        if ind not in r.json().get("values", {}):
            raise RuntimeError(f"Réponse FMI inattendue pour {ind} : {r.text[:200]}")
        contenus[ind] = (gzip.compress(r.content, mtime=0), r.url)
        print(f"  {ind} : {len(r.content):,} octets", file=sys.stderr)
    with Instantane(SOURCE, JEU, date_collecte, None, racine) as inst:
        for ind, (contenu, url) in contenus.items():
            inst.ajouter(f"{ind}.json.gz", contenu, url=url)
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ignorer-existants", action="store_true")
    args = parser.parse_args(argv)
    if args.ignorer_existants and dossier_instantane(SOURCE, JEU, date.today()).exists():
        print("Collecte FMI : déjà collectée aujourd'hui, ignorée", file=sys.stderr)
        return 0
    print("Collecte FMI : Perspectives de l'économie mondiale", file=sys.stderr)
    print(f"  → {collecter()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
