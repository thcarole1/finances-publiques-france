"""F14 — Fait_Projections : projections de la dette par scénario (moteur projection/).

Une ligne par scénario × pays × année. Scénarios : TENDANCIEL (tous les pays), dernière
trajectoire du gouvernement (France), scénarios personnels (scenarios/*.yml), et OBSERVE (les
années observées, pour les graphiques). Non additive (ratios en % du PIB).
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path.cwd()))  # dbt est lancé depuis la racine du dépôt

from projection.scenarios import departs, lire_personnels, tous_les_scenarios  # noqa: E402

COLONNES = [
    "scenario_id",
    "pays_code",
    "date_id",
    "dette_pib",
    "solde_pib",
    "solde_primaire_pib",
    "interets_pib",
    "taux_apparent",
    "taux_10_ans",
    "croissance_volume",
    "croissance_valeur",
    "dette_meur",
    "interets_meur",
    "refinancement_meur",
    "est_projection",
    "source_id",
]


def model(dbt, session):
    dbt.config(materialized="table")
    dette = dbt.ref("fait_dette").df()
    comptes = dbt.ref("fait_comptes_apu_annuels").df()
    transactions = dbt.ref("dim_transaction").df()
    macro = dbt.ref("fait_macro_annuel").df()
    taux = dbt.ref("fait_taux_marche").df()
    gouv = dbt.ref("ref_previsions_gouvernement").df()

    dette = (
        dette.assign(annee=dette.date_id // 10000)
        .groupby(["pays_code", "annee"], as_index=False)["valeur_meur"]
        .sum()
        .rename(columns={"valeur_meur": "dette_meur"})
    )
    c = comptes.merge(transactions[["transaction_code", "sens"]], on="transaction_code")
    c["annee"] = c.date_id // 10000
    c["signe"] = c.valeur_meur.where(c.sens == "Recette", -c.valeur_meur)
    c["interets"] = c.valeur_meur.where(c.transaction_code == "D41_PAY", 0.0)
    comptes = c.groupby(["pays_code", "annee"], as_index=False).agg(
        solde_meur=("signe", "sum"), interets_meur=("interets", "sum")
    )
    macro = macro.assign(annee=macro.date_id // 10000)[
        ["pays_code", "annee", "pib_meur", "croissance_volume_pct"]
    ]
    taux = (
        taux.assign(annee=taux.date_id // 10000)
        .groupby(["pays_code", "annee"], as_index=False)["taux_pct"]
        .mean()
        .rename(columns={"taux_pct": "taux_10_ans"})
    )

    dep = departs(dette, comptes, macro, taux)
    edition = None
    if not gouv.empty:
        derniere = gouv.sort_values(["date_publication", "edition"]).edition.iloc[-1]
        trajectoire = gouv[gouv.edition == derniere]
        edition = (
            "PLF_" + str(int(derniere[:4]) + 1)
            if derniere.endswith("octobre")
            else "RAA_" + derniere[:4]
        )
    else:
        trajectoire = gouv
    personnels = lire_personnels(Path("scenarios"))

    lignes = []
    for sc, resultats in tous_les_scenarios(dep, trajectoire, edition, personnels):
        for r in resultats:
            lignes.append(
                [
                    sc.scenario_id,
                    sc.pays_code,
                    r.annee * 10000 + 1231,
                    r.dette_pib,
                    r.solde_pib,
                    r.solde_primaire_pib,
                    r.interets_pib,
                    r.taux_apparent,
                    r.taux_10_ans,
                    r.croissance_volume,
                    r.croissance_valeur,
                    r.dette_meur,
                    r.interets_meur,
                    r.refinancement_meur,
                    True,
                    "PROJECTION_INTERNE",
                ]
            )
        # Point de départ commun (année observée), pour que les courbes se raccordent.
        d = dep[sc.pays_code]
        lignes.append(
            [
                sc.scenario_id,
                sc.pays_code,
                d.annee * 10000 + 1231,
                100 * d.dette_meur / d.pib_meur,
                None,
                d.solde_primaire_pib,
                None,
                d.taux_apparent,
                d.taux_10_ans,
                None,
                None,
                d.dette_meur,
                None,
                None,
                False,
                "PROJECTION_INTERNE",
            ]
        )

    # Années observées (scénario OBSERVE) depuis 2000.
    obs = dette.merge(macro, on=["pays_code", "annee"]).merge(
        comptes, on=["pays_code", "annee"], how="left"
    )
    obs = obs[(obs.annee >= 2000) & obs.pays_code.isin(dep)]
    for _, o in obs.iterrows():
        pib = o.pib_meur
        lignes.append(
            [
                "OBSERVE",
                o.pays_code,
                int(o.annee) * 10000 + 1231,
                100 * o.dette_meur / pib,
                100 * o.solde_meur / pib if pd.notna(o.solde_meur) else None,
                100 * (o.solde_meur + o.interets_meur) / pib if pd.notna(o.solde_meur) else None,
                100 * o.interets_meur / pib if pd.notna(o.interets_meur) else None,
                None,
                None,
                o.croissance_volume_pct,
                None,
                o.dette_meur,
                o.interets_meur,
                None,
                False,
                "EUROSTAT_GOV_10DD_EDPT1",
            ]
        )

    df = pd.DataFrame(lignes, columns=COLONNES)
    for col in COLONNES[3:14]:
        df[col] = pd.to_numeric(df[col]).round(4)
    df["date_id"] = df.date_id.astype("int32")
    return df.sort_values(["scenario_id", "pays_code", "date_id"]).reset_index(drop=True)
