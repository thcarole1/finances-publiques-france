"""Archivage des instantanés bruts dans les Releases GitHub, et récupération.

Les données brutes ne sont pas versionnées dans Git (docs/02-architecture.md, § 4) : chaque
instantané ``data/raw/<source>/<jeu>/<date>/`` est publié comme une archive ``.tar.gz``
attachée à une Release ``raw-<date>``.

Usage :
    uv run python scripts/donnees_brutes.py publier           # publie les instantanés absents
    uv run python scripts/donnees_brutes.py recuperer          # télécharge les instantanés absents
    uv run python scripts/donnees_brutes.py recuperer --tous   # tous les millésimes (révisions)

``publier`` nécessite ``GITHUB_TOKEN`` (droits ``contents: write``, fourni dans GitHub Actions) ;
``recuperer`` fonctionne sans authentification sur un dépôt public.
Aucune opération ne supprime ni n'écrase un instantané ou une archive existante.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tarfile
import tempfile
from pathlib import Path

import requests

DEPOT = os.environ.get("GITHUB_REPOSITORY", "thcarole1/finances-publiques-france")
RACINE_RAW = Path("data/raw")
API = f"https://api.github.com/repos/{DEPOT}"
MOTIF_ASSET = re.compile(
    r"^(?P<source>[a-z0-9_]+)__(?P<jeu>[a-z0-9_-]+)__(?P<date>\d{4}-\d{2}-\d{2})\.tar\.gz$"
)
# Jeux dont tous les millésimes sont nécessaires (table des révisions, docs/05 F05).
JEUX_TOUS_MILLESIMES = {
    ("eurostat", "gov_10a_main"),
    ("eurostat", "nama_10_gdp"),
    ("fmi", "weo"),  # une édition du FMI par collecte : toutes sont nécessaires (lot 4c)
}


def nom_asset(source: str, jeu: str, date: str) -> str:
    return f"{source}__{jeu}__{date}.tar.gz"


def instantanes_locaux(racine: Path = RACINE_RAW) -> list[tuple[str, str, str, Path]]:
    resultat = []
    for manifeste in sorted(racine.glob("*/*/*/manifest.json")):
        dossier = manifeste.parent
        source, jeu, date = dossier.parts[-3:]
        resultat.append((source, jeu, date, dossier))
    return resultat


def _entetes() -> dict:
    jeton = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    entetes = {"Accept": "application/vnd.github+json"}
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    return entetes


def assets_publies() -> dict[str, str]:
    """Nom d'asset → URL de téléchargement, pour toutes les Releases ``raw-*``."""
    assets: dict[str, str] = {}
    page = 1
    while True:
        r = requests.get(
            f"{API}/releases",
            params={"per_page": 100, "page": page},
            headers=_entetes(),
            timeout=60,
        )
        r.raise_for_status()
        releases = r.json()
        if not releases:
            return assets
        for release in releases:
            if release["tag_name"].startswith("raw-"):
                for a in release["assets"]:
                    assets[a["name"]] = a["url"]
        page += 1


def publier() -> int:
    """Publie chaque instantané local absent des Releases (API REST, jeton GITHUB_TOKEN)."""
    if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
        print("GITHUB_TOKEN requis pour publier (fourni automatiquement dans GitHub Actions).")
        return 1
    deja = assets_publies()
    a_publier = [
        (s, j, d, p) for s, j, d, p in instantanes_locaux() if nom_asset(s, j, d) not in deja
    ]
    if not a_publier:
        print("Aucun nouvel instantané à publier.")
        return 0
    releases: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for source, jeu, date, dossier in a_publier:
            tag = f"raw-{date}"
            if tag not in releases:
                releases[tag] = _release(tag, date)
            archive = Path(tmp) / nom_asset(source, jeu, date)
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(dossier, arcname=f"{source}/{jeu}/{date}")
            url = releases[tag]["upload_url"].split("{")[0]
            r = requests.post(
                url,
                params={"name": archive.name},
                data=archive.read_bytes(),
                headers={**_entetes(), "Content-Type": "application/gzip"},
                timeout=600,
            )
            r.raise_for_status()
            print(f"Publié : {archive.name} → {tag}")
    return 0


def _release(tag: str, date: str) -> dict:
    """Release existante pour ce tag, ou nouvelle Release (jamais modifiée ensuite)."""
    r = requests.get(f"{API}/releases/tags/{tag}", headers=_entetes(), timeout=60)
    if r.status_code == 200:
        return r.json()
    r = requests.post(
        f"{API}/releases",
        json={
            "tag_name": tag,
            "name": f"Données brutes collectées le {date}",
            "body": "Instantanés bruts (docs/02-architecture.md, § 3). Ne pas modifier.",
            "make_latest": "false",
        },
        headers=_entetes(),
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def recuperer(tous: bool = False, racine: Path = RACINE_RAW) -> int:
    disponibles: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for nom, url in assets_publies().items():
        m = MOTIF_ASSET.match(nom)
        if m:
            cle = (m["source"], m["jeu"])
            disponibles.setdefault(cle, []).append((m["date"], nom, url))

    telecharges = 0
    for cle, versions in sorted(disponibles.items()):
        versions.sort()
        choix = versions if (tous or cle in JEUX_TOUS_MILLESIMES) else versions[-1:]
        for date, nom, url in choix:
            cible = racine / cle[0] / cle[1] / date
            if cible.exists():
                continue
            r = requests.get(
                url, headers={**_entetes(), "Accept": "application/octet-stream"}, timeout=600
            )
            r.raise_for_status()
            with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
                membres = tar.getmembers()
                attendu = f"{cle[0]}/{cle[1]}/{date}"
                if any(not m.name.startswith(attendu) or ".." in m.name for m in membres):
                    raise RuntimeError(f"Archive {nom} : contenu inattendu, extraction refusée.")
                tar.extractall(racine, members=membres, filter="data")
            telecharges += 1
            print(f"Récupéré : {nom}")
    print(f"{telecharges} instantané(s) récupéré(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Instantanés bruts ↔ Releases GitHub")
    sous = parser.add_subparsers(dest="commande", required=True)
    sous.add_parser("publier", help="Publier les instantanés locaux absents des Releases")
    rec = sous.add_parser("recuperer", help="Télécharger les instantanés absents en local")
    rec.add_argument("--tous", action="store_true", help="Tous les millésimes de tous les jeux")
    sous.add_parser("lister", help="Lister les instantanés locaux")
    args = parser.parse_args(argv)
    if args.commande == "publier":
        return publier()
    if args.commande == "recuperer":
        return recuperer(args.tous)
    print(json.dumps([f"{s}/{j}/{d}" for s, j, d, _ in instantanes_locaux()], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
