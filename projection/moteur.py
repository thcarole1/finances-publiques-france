"""Moteur de projection de la dette publique, année par année (docs/08, § 3 b).

Principe :

- la dette de départ (fin de l'année de départ) est un « stock ancien » qui garde le taux moyen
  observé et arrive à échéance au rythme de 1/durée de vie moyenne par an ;
- chaque année, ce qui arrive à échéance (stock ancien et nouveaux emprunts) et le besoin de
  financement sont empruntés **au taux de marché** du scénario : une part à court terme (un an),
  le reste à long terme (durée des émissions) ;
- les intérêts d'une année sont payés sur les encours de début d'année ; le solde public est le
  solde hors intérêts moins ces intérêts ; la dette augmente du déficit (et de l'ajustement
  stock-flux).

C'est ce qui reproduit la lenteur de transmission d'une hausse des taux. Sans échéancier titre
par titre (AFT inaccessible), l'amortissement du stock ancien est uniforme : approximation
documentée.

Si un **taux apparent** est imposé pour une année, il remplace le calcul par les encours : avec
un taux apparent et une croissance constants, le moteur redonne exactement la formule fermée du
laboratoire en direct (contrôle croisé, tests/test_projection.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

VARIABLES = [
    "croissance_volume",  # % par an
    "deflateur_pib",  # % par an (à défaut : inflation)
    "inflation",  # % par an
    "taux_10_ans",  # taux de marché des emprunts à long terme, %
    "taux_court",  # taux des emprunts à un an, % (à défaut : taux à 10 ans − 0,5 point)
    "taux_apparent",  # % : s'il est fixé, il remplace le calcul par les encours
    "solde_primaire",  # % du PIB
    "solde_public",  # % du PIB, cible de l'année : le solde hors intérêts en est déduit
    "depense_publique",  # écart en points de PIB : une hausse dégrade le solde hors intérêts
    "prelevements_obligatoires",  # écart en points de PIB : une hausse l'améliore
    "ajustement_stock_flux",  # % du PIB, ajouté à la dette
]


@dataclass
class Depart:
    """Situation observée l'année de départ (fin d'année)."""

    annee: int
    dette_meur: float
    pib_meur: float
    taux_apparent: float  # % : intérêts de l'année / dette de fin d'année précédente
    solde_primaire_pib: float  # %
    taux_10_ans: float  # % (moyenne de l'année)


@dataclass
class Emission:
    part_court_terme: float = 0.10
    maturite_moyenne_emissions: float = 8.0
    duree_vie_stock: float = 8.0  # durée de vie moyenne restante de la dette de départ


@dataclass
class Annee:
    annee: int
    pib_meur: float
    dette_meur: float
    interets_meur: float
    solde_primaire_meur: float
    solde_meur: float
    taux_apparent: float  # %
    taux_10_ans: float  # %
    croissance_volume: float  # %
    croissance_valeur: float  # %
    refinancement_meur: float  # emprunts de l'année (échéances + besoin de financement)

    @property
    def dette_pib(self) -> float:
        return 100 * self.dette_meur / self.pib_meur

    @property
    def solde_pib(self) -> float:
        return 100 * self.solde_meur / self.pib_meur

    @property
    def solde_primaire_pib(self) -> float:
        return 100 * self.solde_primaire_meur / self.pib_meur

    @property
    def interets_pib(self) -> float:
        return 100 * self.interets_meur / self.pib_meur


@dataclass
class Hypotheses:
    """Valeurs annuelles par variable ; une année absente reprend la valeur précédente."""

    valeurs: dict[str, dict[int, float]] = field(default_factory=dict)

    def exacte(self, variable: str, annee: int) -> float | None:
        """Valeur de l'année même, sans report des années précédentes."""
        return self.valeurs.get(variable, {}).get(annee)

    def valeur(self, variable: str, annee: int, defaut: float | None = None) -> float | None:
        serie = self.valeurs.get(variable, {})
        anterieures = [a for a in serie if a <= annee]
        return serie[max(anterieures)] if anterieures else defaut


def projeter(depart: Depart, hyp: Hypotheses, horizon: int, emission: Emission) -> list[Annee]:
    """Projette la dette de depart.annee + 1 à horizon."""
    pib = depart.pib_meur
    dette = depart.dette_meur
    # Encours de début de période : stock ancien (taux observé), émissions longues et courtes.
    ancien, taux_ancien = dette, depart.taux_apparent / 100
    long_terme, taux_long = 0.0, 0.0
    court_terme, taux_court_prec = 0.0, 0.0
    taux_10 = depart.taux_10_ans
    resultats = []
    for annee in range(depart.annee + 1, horizon + 1):
        g_vol = hyp.valeur("croissance_volume", annee, 1.0)
        deflateur = hyp.valeur("deflateur_pib", annee, hyp.valeur("inflation", annee, 1.8))
        taux_10 = hyp.valeur("taux_10_ans", annee, depart.taux_10_ans)
        taux_c = hyp.valeur("taux_court", annee, max(taux_10 - 0.5, 0.0))
        pib_prec = pib
        pib = pib_prec * (1 + g_vol / 100) * (1 + deflateur / 100)

        # Intérêts de l'année, sur les encours de début d'année.
        apparent_impose = hyp.valeur("taux_apparent", annee)
        if apparent_impose is not None:
            interets = dette * apparent_impose / 100
        else:
            interets = ancien * taux_ancien + long_terme * taux_long + court_terme * taux_court_prec

        cible = hyp.exacte("solde_public", annee)
        if cible is not None:
            # Trajectoire officielle : le solde hors intérêts est celui qui donne le solde visé.
            sp_courant = cible + 100 * interets / pib
        elif hyp.exacte("solde_primaire", annee) is not None or not resultats:
            sp_courant = hyp.valeur("solde_primaire", annee, depart.solde_primaire_pib)
        sp_pib = sp_courant
        sp_pib += hyp.valeur("prelevements_obligatoires", annee, 0.0)
        sp_pib -= hyp.valeur("depense_publique", annee, 0.0)
        solde_primaire = pib * sp_pib / 100
        solde = solde_primaire - interets
        asf = pib * hyp.valeur("ajustement_stock_flux", annee, 0.0) / 100

        # Échéances de l'année, refinancées avec le besoin de financement.
        echeance_ancien = min(ancien, depart.dette_meur / emission.duree_vie_stock)
        echeance_long = long_terme / emission.maturite_moyenne_emissions
        echeance_court = court_terme
        a_emprunter = echeance_ancien + echeance_long + echeance_court - solde + asf

        ancien -= echeance_ancien
        reste_long = long_terme - echeance_long
        nouveau_long = a_emprunter * (1 - emission.part_court_terme)
        long_terme = reste_long + nouveau_long
        taux_long = (
            (reste_long * taux_long + nouveau_long * taux_10 / 100) / long_terme
            if long_terme
            else 0.0
        )
        court_terme = a_emprunter * emission.part_court_terme
        taux_court_prec = taux_c / 100

        dette_prec = dette
        dette = dette_prec - solde + asf
        resultats.append(
            Annee(
                annee=annee,
                pib_meur=pib,
                dette_meur=dette,
                interets_meur=interets,
                solde_primaire_meur=solde_primaire,
                solde_meur=solde,
                taux_apparent=100 * interets / dette_prec if dette_prec else 0.0,
                taux_10_ans=taux_10,
                croissance_volume=g_vol,
                croissance_valeur=100 * (pib / pib_prec - 1),
                refinancement_meur=a_emprunter,
            )
        )
    return resultats


def appliquer_surcharges(base: Hypotheses, surcharges: dict, horizon: int) -> Hypotheses:
    """Applique les surcharges d'un scénario (YAML : {variable: {ecart|valeur: {annee: x}}}).

    Un écart s'ajoute à la valeur de base de l'année ; une valeur la remplace. Les années non
    précisées reprennent la base."""
    valeurs = {v: dict(s) for v, s in base.valeurs.items()}
    for variable, modes in surcharges.items():
        serie = valeurs.setdefault(variable, {})
        depart = min([*serie, *(int(a) for m in modes.values() for a in m)], default=None)
        # Matérialise la base année par année avant d'appliquer les écarts.
        complete = (
            {a: base.valeur(variable, a) for a in range(depart, horizon + 1)} if depart else {}
        )
        complete = {a: v for a, v in complete.items() if v is not None}
        for annee, x in (modes.get("valeur") or {}).items():
            complete[int(annee)] = float(x)
        for annee, x in (modes.get("ecart") or {}).items():
            a = int(annee)
            reference = complete.get(a, base.valeur(variable, a, 0.0) or 0.0)
            complete[a] = reference + float(x)
        # Après la dernière surcharge, retour à la base (et non à la dernière valeur surchargée).
        derniere = max(int(a) for m in modes.values() for a in m)
        if derniere < horizon and base.valeur(variable, derniere + 1) is not None:
            complete.setdefault(derniere + 1, base.valeur(variable, derniere + 1))
        valeurs[variable] = complete
    return Hypotheses(valeurs)
