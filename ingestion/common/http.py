"""Client HTTP partagé : en-têtes, délais et nouvelles tentatives."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "finances-publiques-france/0.1 (+https://github.com/thcarole1/finances-publiques-france)"
)
DELAI_PAR_DEFAUT = 60  # secondes


def creer_session(tentatives: int = 5, facteur_attente: float = 2.0) -> requests.Session:
    """Session HTTP avec nouvelles tentatives sur les erreurs transitoires (429, 5xx)."""
    retry = Retry(
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
