"""Client HTTP partagé : en-têtes Retry-After non conformes."""

from ingestion.common.http import RetryTolerant, creer_session


def test_retry_after_decimal_accepte():
    r = RetryTolerant()
    assert r.parse_retry_after("0.000") == 0.0
    assert r.parse_retry_after("2.5") == 2.5


def test_retry_after_entier_et_illisible():
    r = RetryTolerant()
    assert r.parse_retry_after("3") == 3
    assert r.parse_retry_after("bientôt") == 0.0


def test_session_utilise_retry_tolerant():
    adaptateur = creer_session().get_adapter("https://exemple.org")
    assert isinstance(adaptateur.max_retries, RetryTolerant)
