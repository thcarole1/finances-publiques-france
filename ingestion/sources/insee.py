"""Connecteur INSEE : Banque de données macroéconomiques (BDM), API SDMX 2.1 publique.

Usage :
    uv run python -m ingestion.sources.insee                 # tous les jeux
    uv run python -m ingestion.sources.insee dette-trim-apu  # un ou plusieurs jeux

Chaque jeu correspond à un flux (« dataflow ») de la BDM, téléchargé **sans transformation**
(XML SDMX « structure-specific », compressé en gzip) dans
``data/raw/insee/<jeu>/<date_collecte>/`` (voir ``ingestion.common.archivage``).
L'API SDMX de la BDM est publique : aucune clé n'est nécessaire.
"""

from __future__ import annotations

import argparse
import gzip
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ingestion.common.archivage import RACINE_RAW, Instantane, dossier_instantane
from ingestion.common.http import creer_session

URL_BASE = "https://bdm.insee.fr/series/sdmx/data"
SOURCE = "insee"
ANNEE_DEBUT = 1995


@dataclass(frozen=True)
class Jeu:
    code: str
    flux: str
    description: str


JEUX: dict[str, Jeu] = {
    j.code: j
    for j in [
        Jeu(
            "dette-trim-apu",
            "DETTE-TRIM-APU-2020",
            "Dette trimestrielle de Maastricht par sous-secteur (État, organismes, collectivités, "
            "Sécurité sociale) et par instrument, base 2020",
        ),
        Jeu(
            "dette-negociable-etat",
            "DETTE-NEGOCIABLE-ETAT",
            "Dette négociable de l'État : encours mensuel, court / long terme, taux fixe / indexé",
        ),
    ]
}


def verifier_reponse(contenu: bytes) -> None:
    debut = contenu[:2000].decode("utf-8", errors="replace")
    if "<message:StructureSpecificData" not in debut and "StructureSpecificData" not in debut:
        raise RuntimeError(f"Réponse INSEE inattendue : {debut[:300]}")


def collecter(code_jeu: str, date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path:
    jeu = JEUX[code_jeu]
    session = creer_session()
    url = f"{URL_BASE}/{jeu.flux}"
    params = {"startPeriod": str(ANNEE_DEBUT)}
    r = session.get(url, params=params, timeout=600)
    r.raise_for_status()
    verifier_reponse(r.content)
    print(f"  {code_jeu} : {len(r.content):,} octets", file=sys.stderr)
    with Instantane(SOURCE, code_jeu, date_collecte, None, racine) as inst:
        inst.ajouter(
            "donnees.xml.gz", gzip.compress(r.content, mtime=0), url=r.url, parametres=params
        )
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("jeux", nargs="*", default=list(JEUX), help="Jeux à collecter")
    parser.add_argument("--ignorer-existants", action="store_true")
    args = parser.parse_args(argv)
    inconnus = set(args.jeux) - set(JEUX)
    if inconnus:
        parser.error(f"Jeux inconnus : {', '.join(sorted(inconnus))}")
    for code in args.jeux:
        if args.ignorer_existants and dossier_instantane(SOURCE, code, date.today()).exists():
            print(f"Collecte INSEE : {code} déjà collecté aujourd'hui, ignoré", file=sys.stderr)
            continue
        print(f"Collecte INSEE : {code}", file=sys.stderr)
        print(f"  → {collecter(code)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
