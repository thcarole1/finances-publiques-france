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


def test_taxud_integrer_fichier(tmp_path):
    import io
    import zipfile

    from ingestion.sources.taxud import integrer_fichier

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as z:
        z.writestr("x.xml", "<a/>")
    classeur = tmp_path / "ntl.xlsx"
    classeur.write_bytes(tampon.getvalue())
    dossier = integrer_fichier(classeur, "2026", racine=tmp_path / "raw")
    assert (dossier / "ntl.xlsx").read_bytes() == tampon.getvalue()
