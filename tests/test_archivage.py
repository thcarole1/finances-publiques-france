from datetime import date

import pytest

from ingestion.common.archivage import (
    Instantane,
    InstantaneExistantError,
    empreinte_sha256,
    verifier_instantane,
)


def test_instantane_ecrit_fichiers_et_manifeste(tmp_path):
    with Instantane("eurostat", "gov_10a_main", date(2026, 4, 23), racine=tmp_path) as inst:
        inst.ajouter(
            "donnees.csv", b"a,b\n1,2\n", url="https://exemple.org/x", parametres={"geo": "FR"}
        )

    dossier = tmp_path / "eurostat" / "gov_10a_main" / "2026-04-23"
    assert (dossier / "donnees.csv").read_bytes() == b"a,b\n1,2\n"
    manifeste = (dossier / "manifest.json").read_text(encoding="utf-8")
    assert empreinte_sha256(b"a,b\n1,2\n") in manifeste
    assert '"geo": "FR"' in manifeste
    assert verifier_instantane(dossier) == []


def test_instantane_existant_jamais_ecrase(tmp_path):
    with Instantane("insee", "comptes", date(2026, 5, 28), racine=tmp_path) as inst:
        inst.ajouter("f.csv", b"v1", url="u")

    with (
        pytest.raises(InstantaneExistantError),
        Instantane("insee", "comptes", date(2026, 5, 28), racine=tmp_path),
    ):
        pass

    dossier = tmp_path / "insee" / "comptes" / "2026-05-28"
    assert (dossier / "f.csv").read_bytes() == b"v1"


def test_verification_detecte_une_alteration(tmp_path):
    with Instantane("aft", "encours", date(2026, 10, 1), racine=tmp_path) as inst:
        chemin = inst.ajouter("encours.xlsx", b"original", url="u")
    chemin.write_bytes(b"modifie")
    assert verifier_instantane(chemin.parent) == ["empreinte différente : encours.xlsx"]
