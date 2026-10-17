"""Archivage des instantanés bruts et de leur manifeste.

Chaque collecte écrit un dossier ``data/raw/<source>/<jeu>/<date_collecte>/`` contenant les
fichiers tels que téléchargés et un ``manifest.json`` qui permet de retrouver et de vérifier
l'origine de chaque fichier. Un instantané existant n'est jamais écrasé.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

RACINE_RAW = Path("data/raw")
NOM_MANIFESTE = "manifest.json"


class InstantaneExistantError(FileExistsError):
    """Levée quand on tente d'écrire dans un instantané déjà présent."""


@dataclass
class FichierCollecte:
    nom: str
    url: str
    sha256: str
    taille_octets: int
    parametres: dict = field(default_factory=dict)


@dataclass
class Manifeste:
    source: str
    jeu: str
    date_collecte: str
    horodatage_utc: str
    date_publication: str | None = None
    fichiers: list[FichierCollecte] = field(default_factory=list)

    def vers_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def empreinte_sha256(contenu: bytes) -> str:
    return hashlib.sha256(contenu).hexdigest()


def dossier_instantane(
    source: str, jeu: str, date_collecte: date, racine: Path = RACINE_RAW
) -> Path:
    return racine / source / jeu / date_collecte.isoformat()


class Instantane:
    """Écrit les fichiers d'une collecte, puis son manifeste à la fermeture.

    Exemple ::

        with Instantane("eurostat", "gov_10a_main") as inst:
            inst.ajouter("donnees.csv", contenu, url=url, parametres={"geo": "FR"})
    """

    def __init__(
        self,
        source: str,
        jeu: str,
        date_collecte: date | None = None,
        date_publication: str | None = None,
        racine: Path = RACINE_RAW,
    ) -> None:
        self.date_collecte = date_collecte or date.today()
        self.dossier = dossier_instantane(source, jeu, self.date_collecte, racine)
        self.manifeste = Manifeste(
            source=source,
            jeu=jeu,
            date_collecte=self.date_collecte.isoformat(),
            horodatage_utc=datetime.now(UTC).isoformat(timespec="seconds"),
            date_publication=date_publication,
        )

    def __enter__(self) -> Instantane:
        if self.dossier.exists():
            raise InstantaneExistantError(
                f"L'instantané {self.dossier} existe déjà : il n'est jamais écrasé. "
                "Supprimez-le manuellement, après vérification, pour recollecter."
            )
        self.dossier.mkdir(parents=True)
        return self

    def ajouter(self, nom: str, contenu: bytes, url: str, parametres: dict | None = None) -> Path:
        chemin = self.dossier / nom
        if chemin.exists():
            raise InstantaneExistantError(f"Le fichier {chemin} existe déjà dans l'instantané.")
        chemin.write_bytes(contenu)
        self.manifeste.fichiers.append(
            FichierCollecte(
                nom=nom,
                url=url,
                sha256=empreinte_sha256(contenu),
                taille_octets=len(contenu),
                parametres=parametres or {},
            )
        )
        return chemin

    def __exit__(self, exc_type, exc, tb) -> None:
        # Le manifeste est écrit même en cas d'erreur partielle, pour garder la trace
        # de ce qui a été téléchargé ; l'erreur est ensuite propagée.
        (self.dossier / NOM_MANIFESTE).write_text(self.manifeste.vers_json(), encoding="utf-8")


def verifier_instantane(dossier: Path) -> list[str]:
    """Renvoie la liste des anomalies (fichier manquant, empreinte différente)."""
    manifeste = json.loads((dossier / NOM_MANIFESTE).read_text(encoding="utf-8"))
    anomalies = []
    for f in manifeste["fichiers"]:
        chemin = dossier / f["nom"]
        if not chemin.exists():
            anomalies.append(f"manquant : {f['nom']}")
        elif empreinte_sha256(chemin.read_bytes()) != f["sha256"]:
            anomalies.append(f"empreinte différente : {f['nom']}")
    return anomalies
