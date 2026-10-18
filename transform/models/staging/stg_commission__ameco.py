"""Prévisions de la Commission européenne (AMECO), toutes éditions, au format long.

Une ligne par édition × code AMECO × année. Le dernier instantané contient un fichier par
édition (``<année>-<saison>.txt.gz``) : en-tête du fichier AMECO d'origine, puis les lignes des
variables utiles (voir ingestion/sources/commission.py).
"""

import gzip
from pathlib import Path

import pandas as pd

RACINE = Path("data/raw/commission/ameco")


def model(dbt, session):
    dbt.config(materialized="table")
    instantanes = sorted(p for p in RACINE.iterdir() if p.is_dir())
    dernier = instantanes[-1]
    lignes = []
    for fichier in sorted(dernier.glob("*.txt.gz")):
        edition = fichier.name.removesuffix(".txt.gz")
        annees = []
        for ligne in gzip.decompress(fichier.read_bytes()).decode("utf-8").splitlines():
            if ligne.startswith("#") or not ligne.strip():
                continue
            champs = [c.strip() for c in ligne.split(";")]
            if champs[0] == "CODE":
                annees = [(i, int(c)) for i, c in enumerate(champs) if c.isdigit()]
                continue
            code = champs[0]
            for i, annee in annees:
                valeur = champs[i] if i < len(champs) else ""
                if valeur in ("", "NA"):
                    continue
                lignes.append(
                    {
                        "edition": edition,
                        "date_collecte": dernier.name,
                        "code": code,
                        "zone": code.split(".")[0],
                        "variable": code.split(".")[-1],
                        "annee": annee,
                        "valeur": float(valeur),
                    }
                )
    return pd.DataFrame(lignes)
