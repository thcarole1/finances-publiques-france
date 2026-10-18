"""Dim_Scenario : scénarios de projection (observé, tendanciel, gouvernement, personnels)."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path.cwd()))

from projection.scenarios import lire_personnels  # noqa: E402


def model(dbt, session):
    dbt.config(materialized="table")
    gouv = dbt.ref("ref_previsions_gouvernement").df()
    lignes = [
        ("OBSERVE", "Observé", "Observé", None, "Valeurs publiées (Eurostat).", "", 0),
        (
            "TENDANCIEL",
            "Tendanciel (situation actuelle prolongée)",
            "Tendanciel",
            None,
            "Croissance 1 %, inflation 1,8 %, taux à 10 ans et solde hors intérêts de la dernière "
            "année connue, maintenus ; emprunts arrivant à échéance renouvelés au taux du marché.",
            "",
            1,
        ),
    ]
    if not gouv.empty:
        derniere = gouv.sort_values(["date_publication", "edition"]).edition.iloc[-1]
        ident = (
            "PLF_" + str(int(derniere[:4]) + 1)
            if derniere.endswith("octobre")
            else "RAA_" + derniere[:4]
        )
        doc = gouv[gouv.edition == derniere].document.iloc[0]
        lignes.append(
            (
                f"GOUV_{ident}",
                f"Trajectoire du gouvernement ({ident.replace('_', ' ')})",
                "Officiel",
                None,
                f"Croissance et solde public annoncés pour les années publiées, puis solde hors "
                f"intérêts maintenu. Source : {doc}.",
                "",
                2,
            )
        )
    for i, p in enumerate(lire_personnels(Path("scenarios")), start=10):
        lignes.append(
            (
                p["id"],
                p["libelle"],
                "Personnel",
                p["base"],
                (p.get("description") or "").strip(),
                p.get("auteur", ""),
                i,
            )
        )
    df = pd.DataFrame(
        lignes,
        columns=["scenario_id", "libelle", "type", "base", "description", "auteur", "ordre_tri"],
    )
    df["ordre_tri"] = df.ordre_tri.astype("int32")
    return df
