"""Imputation des éliminations de la consolidation aux administrations versantes, par fonction.

Problème : les éliminations (S13_ELIM) sont publiées par fonction COFOG, mais pas par
administration versante ; les transferts versés (Fait_Transferts_APU) sont publiés par
administration, mais pas par fonction. On cherche la matrice administration × fonction qui
respecte les deux marges : c'est un ajustement proportionnel itératif (« raking », méthode RAS),
initialisé par les transferts (D4, D7, D9) de chaque administration dans chaque fonction.

Sortie : pays_code, date_id, sous_secteur_code, fonction, elimination (montant négatif, M€).
"""

import numpy as np
import pandas as pd

ITERATIONS = 50
SOUS_SECTEURS = ["S1311", "S1312", "S1313", "S1314"]


def model(dbt, session):
    dbt.config(materialized="table")
    dep = dbt.ref("fait_depenses_fonction").df()
    cofog = dbt.ref("dim_cofog").df()[["cofog_code", "cofog_n1_libelle"]]
    transferts = dbt.ref("fait_transferts_apu").df()

    dep = dep.merge(cofog, on="cofog_code")
    dep = dep.rename(columns={"cofog_n1_libelle": "fonction"})

    elim = (
        dep[dep.sous_secteur_code == "S13_ELIM"]
        .groupby(["pays_code", "date_id", "fonction"], as_index=False)["valeur_meur"].sum()
    )
    graine = (
        dep[
            dep.sous_secteur_code.isin(SOUS_SECTEURS)
            & dep.transaction_code.isin(["D4_PAY", "D7_PAY", "D9_PAY"])
        ]
        .groupby(["pays_code", "date_id", "sous_secteur_code", "fonction"], as_index=False)[
            "valeur_meur"
        ]
        .sum()
    )
    verses = transferts.groupby(
        ["pays_code", "date_id", "sous_secteur_versant_code"], as_index=False
    )["valeur_meur"].sum()

    resultats = []
    for (pays, date), e in elim.groupby(["pays_code", "date_id"]):
        e = e[e.valeur_meur < -0.05]  # éliminations négatives (le cas normal)
        v = verses[(verses.pays_code == pays) & (verses.date_id == date)]
        v = v[v.valeur_meur > 0.05]
        if e.empty or v.empty:
            continue
        fonctions = list(e.fonction)
        admins = list(v.sous_secteur_versant_code)
        cible_col = -e.set_index("fonction").valeur_meur.reindex(fonctions).to_numpy()
        cible_lig = v.set_index("sous_secteur_versant_code").valeur_meur.reindex(admins).to_numpy()
        # Les deux marges doivent avoir le même total : on ajuste les lignes sur les colonnes.
        cible_lig = cible_lig * cible_col.sum() / cible_lig.sum()

        g = graine[(graine.pays_code == pays) & (graine.date_id == date)]
        m = (
            g.pivot_table(index="sous_secteur_code", columns="fonction", values="valeur_meur",
                          aggfunc="sum")
            .reindex(index=admins, columns=fonctions)
            .fillna(0.0)
            .clip(lower=0.0)
            .to_numpy()
        )
        m = m + 1e-6 * cible_col.sum()  # aucune case strictement nulle : l'ajustement converge
        for _ in range(ITERATIONS):
            m *= (cible_lig / m.sum(axis=1))[:, None]
            m *= (cible_col / m.sum(axis=0))[None, :]

        for i, a in enumerate(admins):
            for j, f in enumerate(fonctions):
                resultats.append((pays, int(date), a, f, -float(m[i, j])))

    return pd.DataFrame(
        resultats,
        columns=["pays_code", "date_id", "sous_secteur_code", "fonction", "elimination"],
    ).astype({"date_id": np.int32})
