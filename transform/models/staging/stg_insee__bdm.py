"""Séries de la BDM de l'INSEE (XML SDMX « structure-specific »), dernier instantané de chaque jeu.

Une ligne par jeu × série (IDBANK) × période. La valeur est convertie dans l'unité de base
(UNIT_MULT : 6 = millions, 9 = milliards), puis exprimée en millions (valeur_m).
"""

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

RACINE = Path("data/raw/insee")


def model(dbt, session):
    dbt.config(materialized="table")
    lignes = []
    for dossier_jeu in sorted(p for p in RACINE.iterdir() if p.is_dir()):
        instantanes = sorted(p for p in dossier_jeu.iterdir() if p.is_dir())
        if not instantanes:
            continue
        dernier = instantanes[-1]
        racine = ET.fromstring(gzip.decompress((dernier / "donnees.xml.gz").read_bytes()))
        for serie in racine.iter("Series"):
            a = serie.attrib
            facteur = 10 ** (int(a.get("UNIT_MULT", "0")) - 6)
            for obs in serie.iter("Obs"):
                o = obs.attrib
                valeur = o.get("OBS_VALUE")
                valeur_m = float(valeur) * facteur if valeur not in (None, "", "NaN") else None
                lignes.append(
                    {
                        "jeu": dossier_jeu.name,
                        "date_collecte": dernier.name,
                        "idbank": a.get("IDBANK"),
                        "titre": a.get("TITLE_FR"),
                        "frequence": a.get("FREQ"),
                        "unite": a.get("UNIT_MEASURE"),
                        "periode": o.get("TIME_PERIOD"),
                        "valeur_m": valeur_m,
                        "statut": o.get("OBS_QUAL"),
                        "date_maj_producteur": a.get("LAST_UPDATE"),
                    }
                )
    return pd.DataFrame(lignes)
