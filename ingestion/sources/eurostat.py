"""Connecteur Eurostat (API SDMX 2.1, format SDMX-CSV compressé).

Usage :
    uv run python -m ingestion.sources.eurostat              # tous les jeux
    uv run python -m ingestion.sources.eurostat gov_10a_exp  # un ou plusieurs jeux

Chaque jeu est téléchargé **sans transformation** et archivé dans un instantané
``data/raw/eurostat/<jeu>/<date_collecte>/`` (voir ``ingestion.common.archivage``).
Les gros jeux sont découpés par pays pour rester sous le seuil au-delà duquel Eurostat
bascule en extraction asynchrone.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from ingestion.common.archivage import RACINE_RAW, Instantane, dossier_instantane
from ingestion.common.http import creer_session

URL_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
FICHIER_PAYS = Path("data/reference/ref_pays.csv")
ANNEE_DEBUT = 1995
SOURCE = "eurostat"

SOUS_SECTEURS = "S13+S1311+S1312+S1313+S1314"


@dataclass(frozen=True)
class Jeu:
    """Un jeu Eurostat et la clé SDMX à interroger.

    ``cle`` est la clé SDMX sans la dimension géographique, qui est toujours la dernière
    dimension des jeux utilisés ici ; ``{geo}`` y est remplacé par la liste des pays.
    """

    code: str
    cle: str
    par_pays: bool = False
    description: str = ""
    parametres: dict = field(default_factory=dict)


JEUX: dict[str, Jeu] = {
    j.code: j
    for j in [
        Jeu(
            "gov_10a_main",
            f"A.MIO_EUR+MIO_NAC.{SOUS_SECTEURS}..{{geo}}",
            par_pays=True,
            description="Principaux agrégats des administrations publiques",
        ),
        Jeu(
            "gov_10a_exp",
            f"A.MIO_EUR+MIO_NAC.{SOUS_SECTEURS}.."
            "TE+D1+P2+D3+D4+D62+D632+D7+D9+P5+NP+D29_D5_D8.{geo}",
            par_pays=True,
            description="Dépenses par fonction (COFOG) et nature",
        ),
        Jeu(
            "gov_10a_taxag",
            f"A.MIO_EUR+MIO_NAC.{SOUS_SECTEURS}..{{geo}}",
            par_pays=True,
            description="Recettes fiscales et cotisations sociales détaillées",
        ),
        Jeu(
            "nama_10_gdp",
            "A.CP_MEUR+CP_MNAC+CLV_PCH_PRE+PD_PCH_PRE_EUR.B1GQ.{geo}",
            description="PIB (prix courants, volume, prix)",
        ),
        Jeu(
            "gov_10dd_edpt1",
            f"A.MIO_EUR+MIO_NAC.{SOUS_SECTEURS}.GD+GD_F2+GD_F31+GD_F32+GD_F41+GD_F42.{{geo}}",
            description="Dette publique notifiée (procédure de déficit excessif), par instrument",
        ),
        Jeu(
            "gov_10dd_ggd",
            "A.GD.S1+S11_S14_S15+S121+S122_S123+S124-S129+S1_S2+S2.S13.TOTAL.MIO_EUR+MIO_NAC.{geo}",
            description="Dette publique par détenteur",
        ),
        Jeu(
            "irt_lt_mcby_m",
            "M.MCBY.{geo}",
            description="Taux d'intérêt à long terme (emprunts d'État à 10 ans), mensuel",
        ),
        Jeu(
            "gov_10q_ggdebt",
            f"Q.GD.{SOUS_SECTEURS}.MIO_EUR+MIO_NAC+PC_GDP.{{geo}}",
            description="Dette publique trimestrielle par sous-secteur",
        ),
        Jeu(
            "gov_10q_ggnfa",
            "Q.MIO_EUR+MIO_NAC+PC_GDP.NSA+SCA.S13.TE+TR+B9+D41PAY.{geo}",
            description="Comptes trimestriels des administrations (dépenses, recettes, solde)",
        ),
        Jeu(
            "namq_10_gdp",
            "Q.CP_MEUR+CP_MNAC.NSA+SCA.B1GQ.{geo}",
            description="PIB trimestriel à prix courants, brut et CVS",
        ),
        Jeu(
            "nama_10_pe",
            "A.THS_PER.POP_NC.{geo}",
            description="Population (comptabilité nationale, moyenne annuelle)",
        ),
    ]
}


class ExtractionAsynchroneError(RuntimeError):
    """Eurostat a mis la requête en file d'attente au lieu de renvoyer les données."""


def codes_pays(fichier: Path = FICHIER_PAYS) -> list[str]:
    """Codes Eurostat des pays et agrégats dont Eurostat est la source de référence."""
    with fichier.open(encoding="utf-8") as f:
        return [
            r["code_eurostat"]
            for r in csv.DictReader(f)
            if r["source_reference"] == "Eurostat" and r["code_eurostat"]
        ]


def construire_url(jeu: Jeu, geos: list[str]) -> tuple[str, dict]:
    cle = jeu.cle.format(geo="+".join(geos))
    params = {
        "format": "SDMX-CSV",
        "compressed": "true",
        "startPeriod": str(ANNEE_DEBUT),
        **jeu.parametres,
    }
    return f"{URL_BASE}/{jeu.code}/{cle}", params


def verifier_reponse(contenu: bytes) -> None:
    """Refuse une réponse qui n'est pas un CSV compressé (file d'attente, erreur SOAP)."""
    if contenu[:2] == b"\x1f\x8b":
        return
    extrait = contenu[:500].decode("utf-8", errors="replace")
    if "queued" in extrait or "SUBMITTED" in extrait:
        raise ExtractionAsynchroneError(
            "Eurostat a placé la requête en extraction asynchrone (volume trop important). "
            "Découper la requête (par_pays=True) ou réduire la clé."
        )
    raise RuntimeError(f"Réponse Eurostat inattendue : {extrait}")


def geos_refuses(reponse) -> list[str]:
    """Pays refusés par Eurostat (erreur 400 « GEO=XX not allowed ») ; liste vide sinon."""
    if reponse.status_code != 400:
        return []
    return re.findall(r"GEO=([A-Z0-9_]+)", reponse.text)


def date_mise_a_jour(contenu_gz: bytes) -> str | None:
    """Date de dernière mise à jour publiée par Eurostat (colonne LAST UPDATE), au format ISO."""
    texte = gzip.decompress(contenu_gz).decode("utf-8")
    lecteur = csv.DictReader(io.StringIO(texte))
    dates = set()
    for ligne in lecteur:
        valeur = ligne.get("LAST UPDATE")
        if valeur:
            dates.add(valeur)
    if not dates:
        return None
    # Format Eurostat : JJ/MM/AA HH:MM:SS
    return max(datetime.strptime(d, "%d/%m/%y %H:%M:%S") for d in dates).date().isoformat()


def collecter(code_jeu: str, date_collecte: date | None = None, racine: Path = RACINE_RAW) -> Path:
    jeu = JEUX[code_jeu]
    session = creer_session()
    geos = codes_pays()
    lots = [[g] for g in geos] if jeu.par_pays else [geos]

    telechargements: list[tuple[str, bytes, str, dict]] = []
    for lot in lots:
        url, params = construire_url(jeu, lot)
        reponse = session.get(url, params=params, timeout=600)
        refuses = geos_refuses(reponse)
        if refuses:
            # Certains jeux ne couvrent pas tous les pays (Norvège, Suisse…) : Eurostat refuse
            # alors toute la requête. On retire les pays refusés et on réessaie.
            print(
                f"  {code_jeu} : pays absents du jeu, ignorés : {', '.join(refuses)}",
                file=sys.stderr,
            )
            lot = [g for g in lot if g not in refuses]
            if not lot:
                continue
            url, params = construire_url(jeu, lot)
            reponse = session.get(url, params=params, timeout=600)
        if reponse.status_code == 404:
            # Eurostat renvoie 404 quand aucune donnée ne correspond (pays absent du jeu).
            print(f"  {code_jeu} {'+'.join(lot)} : aucune donnée", file=sys.stderr)
            continue
        reponse.raise_for_status()
        verifier_reponse(reponse.content)
        nom = f"{lot[0]}.csv.gz" if jeu.par_pays else "donnees.csv.gz"
        telechargements.append((nom, reponse.content, reponse.url, params))
        print(f"  {code_jeu} {nom} : {len(reponse.content):,} octets", file=sys.stderr)

    if not telechargements:
        raise RuntimeError(f"Aucune donnée téléchargée pour {code_jeu}")

    publication = max(
        (d for _, contenu, _, _ in telechargements if (d := date_mise_a_jour(contenu))),
        default=None,
    )
    with Instantane(SOURCE, code_jeu, date_collecte, publication, racine) as inst:
        for nom, contenu, url, params in telechargements:
            inst.ajouter(nom, contenu, url=url, parametres=params)
    return inst.dossier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("jeux", nargs="*", default=list(JEUX), help="Jeux à collecter")
    parser.add_argument(
        "--ignorer-existants",
        action="store_true",
        help="Ne pas recollecter un jeu déjà collecté aujourd'hui (au lieu d'échouer)",
    )
    args = parser.parse_args(argv)
    inconnus = set(args.jeux) - set(JEUX)
    if inconnus:
        parser.error(f"Jeux inconnus : {', '.join(sorted(inconnus))}")
    for code in args.jeux:
        if args.ignorer_existants and dossier_instantane(SOURCE, code, date.today()).exists():
            print(f"Collecte Eurostat : {code} déjà collecté aujourd'hui, ignoré", file=sys.stderr)
            continue
        print(f"Collecte Eurostat : {code}", file=sys.stderr)
        dossier = collecter(code)
        print(f"  → {dossier}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
