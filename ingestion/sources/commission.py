"""Connecteur Commission européenne : prévisions économiques (base AMECO), toutes éditions.

Usage :
    uv run python -m ingestion.sources.commission

AMECO est republiée à chaque prévision de la Commission (printemps, automne, et certains hivers).
Les éditions passées restent téléchargeables sur la page « AMECO archive ». Chaque édition est
une archive ZIP d'environ 7 Mo (18 fichiers texte) ; on n'en conserve que les **lignes** des
variables utilisées par le modèle, **sans modifier les valeurs**, précédées de la ligne d'en-tête
du fichier d'origine :

- UDGG  : dette publique (au sens de Maastricht), en % du PIB ;
- UBLGE : solde public (procédure de déficit excessif), en % du PIB ;
- UBLGIE: solde hors intérêts, en % du PIB ;
- OVGD  : PIB en volume (pour calculer la croissance prévue).

Un instantané ``data/raw/commission/ameco/<date>/`` contient un fichier par édition. Une édition
déjà présente dans l'instantané précédent est reprise telle quelle (pas de nouveau
téléchargement) ; aucun instantané n'est créé si aucune édition n'est nouvelle.
"""

from __future__ import annotations

import argparse
import gzip
import io
import re
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests

from ingestion.common.archivage import RACINE_RAW, Instantane
from ingestion.common.http import creer_session

SOURCE = "commission"
JEU = "ameco"
SITE = "https://economy-finance.ec.europa.eu"
PAGE_ARCHIVE = (
    f"{SITE}/economic-research-and-databases/economic-databases/ameco-database/ameco-archive_en"
)
PAGE_COURANTE = (
    f"{SITE}/economic-research-and-databases/economic-databases/ameco-database/"
    "download-annual-data-set-macro-economic-database-ameco_en"
)
SAISONS = {"spring": "printemps", "autumn": "automne", "winter": "hiver"}
LIGNE_UTILE = re.compile(r"^[A-Z0-9_]+\.1\.(0\.319\.0\.(UDGG|UBLGE|UBLGIE)|1\.0\.0\.OVGD);")
PAUSE = 12  # secondes entre deux téléchargements (le site limite le débit)


class AucuneVariableError(RuntimeError):
    """L'archive ne contient aucune des variables utilisées (prévisions d'hiver)."""


@dataclass(frozen=True)
class Edition:
    identifiant: str  # « 2024-printemps »
    url: str


def identifiant(libelle: str) -> str | None:
    m = re.search(r"(Spring|Autumn|Winter)\s+(\d{4})", libelle, re.IGNORECASE)
    return f"{m[2]}-{SAISONS[m[1].lower()]}" if m else None


def editions_archive(page_html: str) -> list[Edition]:
    editions: dict[str, Edition] = {}
    for href, libelle in re.findall(
        r'<a href="(/document/download/[^"]+)"[^>]*data-untranslated-label="([^"]+)"', page_html
    ):
        ident = identifiant(libelle)
        if ident and "coverage" not in libelle.lower() and ident not in editions:
            editions[ident] = Edition(ident, urljoin(SITE, href))
    return list(editions.values())


def edition_courante(page_html: str) -> Edition:
    texte = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page_html))
    m = re.search(r"Last update:[^-]*-\s*((Spring|Autumn|Winter)\s+\d{4})", texte, re.IGNORECASE)
    lien = re.search(
        r'<a href="(/document/download/[^"]+)"[^>]*data-untranslated-label="AMECO - All zipped TXT',
        page_html,
    )
    if not (m and lien):
        raise RuntimeError("Édition courante d'AMECO introuvable sur la page de téléchargement.")
    return Edition(identifiant(m[1]), urljoin(SITE, lien[1]))


def extraire(contenu_zip: bytes) -> bytes:
    """En-têtes et lignes des variables utiles, dans l'ordre des fichiers de l'archive."""
    sortie = io.StringIO()
    with zipfile.ZipFile(io.BytesIO(contenu_zip)) as z:
        noms = z.namelist()
        if not any(n.upper().endswith(".TXT") for n in noms):
            # Certaines éditions (2020-2022) emballent les fichiers dans des archives internes :
            # « ameco0.zip » contient l'ensemble des données.
            interne = next((n for n in noms if n.lower() == "ameco0.zip"), None)
            if interne:
                return extraire(z.read(interne))
        for nom in sorted(noms):
            if not nom.upper().endswith(".TXT"):
                continue
            lignes = z.read(nom).decode("latin-1").splitlines()
            utiles = [ligne for ligne in lignes[1:] if LIGNE_UTILE.match(ligne)]
            if utiles:
                sortie.write(f"# {nom}\n{lignes[0]}\n" + "\n".join(utiles) + "\n")
    if not sortie.getvalue():
        raise AucuneVariableError("Aucune variable utile trouvée dans l'archive AMECO.")
    return sortie.getvalue().encode("utf-8")


def telecharger(session, e: Edition, essais: int = 5) -> bytes:
    """Télécharge une archive, avec nouvelles tentatives si la connexion est coupée."""
    for essai in range(1, essais + 1):
        try:
            r = session.get(e.url, timeout=600)
            r.raise_for_status()
            if r.content[:2] != b"PK":
                raise RuntimeError(f"la réponse n'est pas une archive ZIP ({e.url})")
            return r.content
        except (
            requests.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            RuntimeError,
        ) as exc:
            if essai == essais:
                raise RuntimeError(
                    f"{e.identifiant} : échec après {essais} essais ({exc})"
                ) from exc
            print(
                f"  {e.identifiant} : essai {essai} échoué ({exc}), nouvel essai", file=sys.stderr
            )
            time.sleep(PAUSE * essai)
    raise AssertionError("inaccessible")


def dernier_instantane(racine: Path) -> Path | None:
    dossier = racine / SOURCE / JEU
    instantanes = sorted(p for p in dossier.iterdir() if p.is_dir()) if dossier.exists() else []
    return instantanes[-1] if instantanes else None


def collecter(date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path | None:
    session = creer_session(tentatives=8, facteur_attente=5)
    archive = session.get(PAGE_ARCHIVE, timeout=120)
    archive.raise_for_status()
    courante = session.get(PAGE_COURANTE, timeout=120)
    courante.raise_for_status()
    editions = editions_archive(archive.text)
    actuelle = edition_courante(courante.text)
    if actuelle.identifiant not in {e.identifiant for e in editions}:
        editions.insert(0, actuelle)

    precedent = dernier_instantane(racine)
    deja = (
        {p.name.removesuffix(".txt.gz"): p for p in precedent.glob("*.txt.gz")} if precedent else {}
    )
    nouvelles = [e for e in editions if e.identifiant not in deja]
    if not nouvelles:
        print("  aucune nouvelle édition AMECO", file=sys.stderr)
        return None

    # Tout est téléchargé avant d'écrire l'instantané : une coupure en cours de route ne laisse
    # pas d'instantané incomplet.
    contenus: dict[str, tuple[bytes, dict]] = {}
    ignorees: set[str] = set()
    for e in nouvelles:
        contenu_zip = telecharger(session, e)
        try:
            extrait = extraire(contenu_zip)
        except AucuneVariableError:
            # Les prévisions d'hiver ne portent que sur la croissance et l'inflation, publiées
            # sous un autre format : elles sont ignorées (aucune variable de finances publiques).
            print(f"  {e.identifiant} : aucune variable utile, édition ignorée", file=sys.stderr)
            ignorees.add(e.identifiant)
            time.sleep(PAUSE)
            continue
        contenus[e.identifiant] = (
            gzip.compress(extrait, mtime=0),
            {"variables": "UDGG UBLGE UBLGIE (% du PIB), OVGD"},
        )
        print(f"  {e.identifiant} : {len(contenu_zip):,} octets", file=sys.stderr)
        time.sleep(PAUSE)

    with Instantane(SOURCE, JEU, date_collecte, None, racine) as inst:
        for e in sorted(editions, key=lambda e: e.identifiant):
            if e.identifiant in ignorees:
                continue
            nom = f"{e.identifiant}.txt.gz"
            if e.identifiant in contenus:
                contenu, parametres = contenus[e.identifiant]
            else:
                contenu, parametres = (
                    deja[e.identifiant].read_bytes(),
                    {"repris_de": precedent.name},
                )
            inst.ajouter(nom, contenu, url=e.url, parametres=parametres)
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--ignorer-existants",
        action="store_true",
        help="Sans effet : seules les éditions nouvelles sont téléchargées.",
    )
    parser.parse_args(argv)
    print("Collecte Commission européenne : prévisions (AMECO)", file=sys.stderr)
    dossier = collecter()
    print(f"  → {dossier or 'rien de nouveau'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
