"""Client HTTP partagé : en-têtes, délais et nouvelles tentatives."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "finances-publiques-france/0.1 (+https://github.com/thcarole1/finances-publiques-france)"
)
DELAI_PAR_DEFAUT = 60  # secondes


class RetryTolerant(Retry):
    """Nouvelles tentatives qui acceptent un en-tête Retry-After décimal (« 0.000 »).

    La norme n'admet qu'un nombre entier de secondes ou une date ; certains serveurs (DG TAXUD,
    novembre 2026) renvoient un décimal, que urllib3 rejette en interrompant la collecte. Une
    valeur illisible est ignorée : l'attente progressive (backoff) s'applique alors."""

    def parse_retry_after(self, retry_after: str) -> float:
        try:
            return super().parse_retry_after(retry_after)
        except Exception:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                return 0.0


def creer_session(tentatives: int = 5, facteur_attente: float = 2.0) -> requests.Session:
    """Session HTTP avec nouvelles tentatives sur les erreurs transitoires (429, 5xx)."""
    retry = RetryTolerant(
        total=tentatives,
        backoff_factor=facteur_attente,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
