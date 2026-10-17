"""Génère data/reference/ref_glossaire.csv à partir de docs/glossaire.md (source unique).

Usage : uv run python scripts/generer_glossaire.py [--verifier]
Avec --verifier : code de sortie 1 si le CSV n'est pas à jour (utilisé en CI).
"""

from __future__ import annotations

import csv
import io
import re
import sys
import unicodedata
from pathlib import Path

SOURCE = Path("docs/glossaire.md")
CIBLE = Path("data/reference/ref_glossaire.csv")


def identifiant(terme: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", terme).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sans_accents.lower()).strip("-")


def lire_glossaire(texte: str) -> list[dict]:
    entrees = []
    for bloc in re.split(r"^### ", texte, flags=re.M)[1:]:
        lignes = bloc.strip().splitlines()
        terme = lignes[0].strip()
        corps = "\n".join(lignes[1:])
        court = re.search(r"\*\*Court :\*\*\s*(.+?)(?=\n\s*\n|\Z)", corps, re.S)
        long = re.search(r"\*\*Long :\*\*\s*(.+?)(?=\n\s*\n|\Z)", corps, re.S)
        entrees.append(
            {
                "glossaire_id": identifiant(terme),
                "terme": terme,
                "definition_courte": " ".join(court.group(1).split()) if court else "",
                "definition_longue": " ".join(long.group(1).split()) if long else "",
            }
        )
    entrees.sort(key=lambda e: e["terme"].lower())
    for i, e in enumerate(entrees, 1):
        e["ordre_tri"] = i
    return entrees


def rendre_csv(entrees: list[dict]) -> str:
    sortie = io.StringIO()
    w = csv.DictWriter(sortie, fieldnames=list(entrees[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(entrees)
    return sortie.getvalue()


def main() -> int:
    contenu = rendre_csv(lire_glossaire(SOURCE.read_text(encoding="utf-8")))
    if "--verifier" in sys.argv:
        if not CIBLE.exists() or CIBLE.read_text(encoding="utf-8") != contenu:
            print("ref_glossaire.csv n'est pas à jour : lancer scripts/generer_glossaire.py")
            return 1
        print("Glossaire à jour.")
        return 0
    CIBLE.write_text(contenu, encoding="utf-8")
    print(f"{CIBLE} : {contenu.count(chr(10)) - 1} termes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
