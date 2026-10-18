"""Scénarios de projection : situation de départ, scénarios de base, scénarios personnels.

- **TENDANCIEL** (tous les pays) : croissance 1 %, inflation 1,8 %, taux à 10 ans et solde hors
  intérêts de l'année de départ, maintenus sur l'horizon (mêmes valeurs par défaut que le
  laboratoire en direct, mais avec refinancement explicite).
- **GOUV_<édition>** (France) : dernière trajectoire du gouvernement (ref_previsions_gouvernement) ;
  croissance et solde public visés pour les années publiées, puis solde hors intérêts maintenu.
- **Scénarios personnels** (scenarios/*.yml) : surcharges d'un scénario de base.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from projection.moteur import Annee, Depart, Emission, Hypotheses, appliquer_surcharges, projeter

HORIZON_BASE = 10  # années après l'année de départ pour les scénarios de base
CROISSANCE_DEFAUT = 1.0
INFLATION_DEFAUT = 1.8


@dataclass
class Scenario:
    scenario_id: str
    libelle: str
    type: str  # Observé, Tendanciel, Officiel, Personnel
    pays_code: str
    base: str | None
    description: str
    auteur: str
    horizon: int
    hypotheses: Hypotheses
    emission: Emission


def departs(
    dette: pd.DataFrame, comptes: pd.DataFrame, macro: pd.DataFrame, taux: pd.DataFrame
) -> dict[str, Depart]:
    """Situation de la dernière année de dette publiée, pour chaque pays.

    dette : pays_code, annee, dette_meur ; comptes : pays_code, annee, solde_meur, interets_meur ;
    macro : pays_code, annee, pib_meur ; taux : pays_code, annee, taux_10_ans."""
    resultat = {}
    for pays, d in dette.groupby("pays_code"):
        d = d.set_index("annee")["dette_meur"]
        t0 = int(d.index.max())
        c = comptes[(comptes.pays_code == pays) & (comptes.annee == t0)]
        m = macro[(macro.pays_code == pays) & (macro.annee == t0)]
        if c.empty or m.empty or (t0 - 1) not in d.index:
            continue
        pib = float(m.pib_meur.iloc[0])
        interets = float(c.interets_meur.iloc[0])
        apparent = 100 * interets / float(d.loc[t0 - 1])
        t = taux[(taux.pays_code == pays) & (taux.annee == t0)]
        resultat[pays] = Depart(
            annee=t0,
            dette_meur=float(d.loc[t0]),
            pib_meur=pib,
            taux_apparent=apparent,
            solde_primaire_pib=100 * (float(c.solde_meur.iloc[0]) + interets) / pib,
            taux_10_ans=float(t.taux_10_ans.iloc[0]) if not t.empty else apparent + 1.0,
        )
    return resultat


def hypotheses_tendancielles(depart: Depart) -> Hypotheses:
    a = depart.annee + 1
    return Hypotheses(
        {
            "croissance_volume": {a: CROISSANCE_DEFAUT},
            "inflation": {a: INFLATION_DEFAUT},
            "taux_10_ans": {a: depart.taux_10_ans},
            "solde_primaire": {a: depart.solde_primaire_pib},
        }
    )


def hypotheses_gouvernement(depart: Depart, trajectoire: pd.DataFrame) -> Hypotheses:
    """trajectoire : variable_code (CROISSANCE, SOLDE), annee, valeur — une édition."""
    hyp = hypotheses_tendancielles(depart)
    for variable, cle in [("CROISSANCE", "croissance_volume"), ("SOLDE", "solde_public")]:
        lignes = trajectoire[
            (trajectoire.variable_code == variable) & (trajectoire.annee > depart.annee)
        ]
        for _, ligne in lignes.iterrows():
            hyp.valeurs.setdefault(cle, {})[int(ligne.annee)] = float(ligne.valeur)
    if "solde_public" in hyp.valeurs:
        # Le solde hors intérêts découle des cibles de solde : on ne fixe que sa valeur initiale.
        hyp.valeurs["solde_primaire"] = {}
    return hyp


def figer_base(hyp: Hypotheses, resultats: list[Annee]) -> Hypotheses:
    """Hypothèses de base « figées » année par année, à partir de la projection de base : les
    écarts d'un scénario personnel s'appliquent alors à des valeurs connues pour chaque année."""
    valeurs = {v: {} for v in ["croissance_volume", "inflation", "taux_10_ans", "solde_primaire"]}
    for r in resultats:
        valeurs["croissance_volume"][r.annee] = r.croissance_volume
        valeurs["taux_10_ans"][r.annee] = r.taux_10_ans
        valeurs["solde_primaire"][r.annee] = r.solde_primaire_pib
        valeurs["inflation"][r.annee] = hyp.valeur("inflation", r.annee, INFLATION_DEFAUT)
    return Hypotheses(valeurs)


def lire_personnels(dossier: Path) -> list[dict]:
    from scripts.valider_scenarios import normaliser_cles

    return [
        normaliser_cles(yaml.safe_load(f.read_text(encoding="utf-8")))
        for f in sorted(dossier.glob("*.yml"))
    ]


def tous_les_scenarios(
    dep: dict[str, Depart],
    gouvernement: pd.DataFrame,
    edition_gouv: str | None,
    personnels: list[dict],
) -> list[tuple[Scenario, list[Annee]]]:
    sorties: list[tuple[Scenario, list[Annee]]] = []
    bases: dict[tuple[str, str], tuple[Hypotheses, list[Annee], int]] = {}
    for pays, d in sorted(dep.items()):
        horizon = d.annee + HORIZON_BASE
        hyp = hypotheses_tendancielles(d)
        res = projeter(d, hyp, horizon, Emission())
        sc = Scenario(
            "TENDANCIEL",
            "Tendanciel (situation actuelle prolongée)",
            "Tendanciel",
            pays,
            None,
            "Croissance 1 %, inflation 1,8 %, taux à 10 ans et solde hors intérêts de l'année "
            "de départ maintenus ; emprunts renouvelés au taux du marché.",
            "",
            horizon,
            hyp,
            Emission(),
        )
        sorties.append((sc, res))
        bases[("TENDANCIEL", pays)] = (hyp, res, horizon)
        if pays == "FR" and edition_gouv:
            hyp_g = hypotheses_gouvernement(d, gouvernement)
            res_g = projeter(d, hyp_g, horizon, Emission())
            ident = f"GOUV_{edition_gouv}"
            sc = Scenario(
                ident,
                f"Trajectoire du gouvernement ({edition_gouv.replace('_', ' ')})",
                "Officiel",
                pays,
                None,
                "Croissance et solde public annoncés par le gouvernement pour les années "
                "publiées, puis solde hors intérêts maintenu.",
                "",
                horizon,
                hyp_g,
                Emission(),
            )
            sorties.append((sc, res_g))
            bases[(ident, pays)] = (hyp_g, res_g, horizon)

    for p in personnels:
        pays = p.get("pays", "FR")
        if (p["base"], pays) not in bases:
            raise ValueError(f"{p['id']} : scénario de base inconnu {p['base']} pour {pays}")
        hyp_b, res_b, _ = bases[(p["base"], pays)]
        horizon = int(p["horizon"])
        d = dep[pays]
        base_figee = figer_base(
            hyp_b,
            projeter(d, hyp_b, horizon, Emission()) if horizon > len(res_b) + d.annee else res_b,
        )
        hyp = appliquer_surcharges(base_figee, p["hypotheses"], horizon)
        em = Emission(**{k: float(v) for k, v in (p.get("emission") or {}).items()})
        sc = Scenario(
            p["id"],
            p["libelle"],
            "Personnel",
            pays,
            p["base"],
            (p.get("description") or "").strip(),
            p.get("auteur", ""),
            horizon,
            hyp,
            em,
        )
        sorties.append((sc, projeter(d, hyp, horizon, em)))
    return sorties
