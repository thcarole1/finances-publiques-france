"""Prévisions du FMI (Perspectives de l'économie mondiale), une édition par collecte.

L'API ne sert que l'édition en vigueur : chaque instantané est rattaché à l'édition d'avril
(collecte d'avril à septembre) ou d'octobre (collecte d'octobre à mars). Si plusieurs
instantanés relèvent de la même édition, le plus récent est retenu.
"""

import gzip
import json
from datetime import date
from pathlib import Path

import pandas as pd

RACINE = Path("data/raw/fmi/weo")


def edition(jour: date) -> str:
    if 4 <= jour.month <= 9:
        return f"{jour.year}-avril"
    return f"{jour.year if jour.month >= 10 else jour.year - 1}-octobre"


def model(dbt, session):
    dbt.config(materialized="table")
    retenus = {}
    for dossier in sorted(p for p in RACINE.iterdir() if p.is_dir()):
        retenus[edition(date.fromisoformat(dossier.name))] = dossier  # le plus récent l'emporte
    lignes = []
    for ed, dossier in sorted(retenus.items()):
        for fichier in sorted(dossier.glob("*.json.gz")):
            indicateur = fichier.name.removesuffix(".json.gz")
            valeurs = json.loads(gzip.decompress(fichier.read_bytes()))["values"][indicateur]
            for zone, serie in valeurs.items():
                for annee, valeur in serie.items():
                    if valeur is None:
                        continue
                    lignes.append(
                        {
                            "edition": ed,
                            "date_collecte": dossier.name,
                            "zone": zone,
                            "variable": indicateur,
                            "annee": int(annee),
                            "valeur": float(valeur),
                        }
                    )
    return pd.DataFrame(lignes)
