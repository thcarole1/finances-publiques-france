"""Valide les scénarios personnels (contrôle QC-B11).

Usage : uv run python scripts/valider_scenarios.py [dossier]
Code de sortie 1 si un scénario est invalide.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

DOSSIER_PAR_DEFAUT = Path("scenarios")


def valider_dossier(dossier: Path) -> list[str]:
    schema = json.loads((dossier / "_schema.json").read_text(encoding="utf-8"))
    validateur = Draft202012Validator(schema)
    erreurs: list[str] = []
    identifiants: dict[str, Path] = {}

    for fichier in sorted(dossier.glob("*.yml")):
        try:
            contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            erreurs.append(f"{fichier.name} : YAML illisible ({exc})")
            continue

        contenu = normaliser_cles(contenu)
        for err in validateur.iter_errors(contenu):
            chemin = "/".join(str(p) for p in err.absolute_path) or "(racine)"
            erreurs.append(f"{fichier.name} : {chemin} : {err.message}")

        if not isinstance(contenu, dict):
            continue
        ident = contenu.get("id")
        if ident in identifiants:
            erreurs.append(
                f"{fichier.name} : identifiant {ident} déjà utilisé par {identifiants[ident].name}"
            )
        elif ident:
            identifiants[ident] = fichier

        horizon = contenu.get("horizon")
        for variable, modes in (contenu.get("hypotheses") or {}).items():
            if not isinstance(modes, dict):
                continue
            ecarts = set((modes.get("ecart") or {}).keys())
            valeurs = set((modes.get("valeur") or {}).keys())
            for annee in sorted(ecarts & valeurs):
                erreurs.append(
                    f"{fichier.name} : hypotheses/{variable}/{annee} est à la fois un écart "
                    "et une valeur"
                )
            for annee in sorted(ecarts | valeurs):
                if isinstance(horizon, int) and annee.isdigit() and int(annee) > horizon:
                    erreurs.append(
                        f"{fichier.name} : hypotheses/{variable}/{annee} "
                        f"dépasse l'horizon {horizon}"
                    )
    return erreurs


def normaliser_cles(objet):
    """YAML lit `2027:` comme un entier : on convertit toutes les clés en texte."""
    if isinstance(objet, dict):
        return {str(k): normaliser_cles(v) for k, v in objet.items()}
    if isinstance(objet, list):
        return [normaliser_cles(v) for v in objet]
    return objet


def main() -> int:
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else DOSSIER_PAR_DEFAUT
    erreurs = valider_dossier(dossier)
    if erreurs:
        print("Scénarios invalides :")
        for e in erreurs:
            print(f"  - {e}")
        return 1
    print(f"Scénarios valides ({len(list(dossier.glob('*.yml')))} fichier(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
