"""Valide les fichiers du rapport Power BI (format PBIR) contre les schémas JSON officiels.

Power BI Desktop refuse d'ouvrir un rapport dont un fichier ne respecte pas son schéma. Ce
script reproduit ce contrôle avant l'ouverture, en CI et en local.

Les schémas sont publiés par Microsoft dans le dépôt GitHub microsoft/json-schemas. Leurs
adresses ($schema, $ref) pointent vers developer.microsoft.com : on les résout vers une copie
locale de ce dépôt, sans accès réseau.

Usage :
    git clone --depth 1 --filter=blob:none --sparse https://github.com/microsoft/json-schemas \\
        /tmp/json-schemas && git -C /tmp/json-schemas sparse-checkout set fabric/item/report
    uv run python scripts/valider_pbir.py --schemas /tmp/json-schemas
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

PREFIXE = "https://developer.microsoft.com/json-schemas/"
RAPPORT = Path("powerbi/FinancesPubliques.Report/definition")


def registre(depot_schemas: Path) -> Registry:
    def recuperer(uri: str) -> Resource:
        if not uri.startswith(PREFIXE):
            raise Unresolvable(uri)
        chemin = depot_schemas / uri[len(PREFIXE) :].split("#")[0]
        return Resource.from_contents(json.loads(chemin.read_text(encoding="utf-8")))

    return Registry(retrieve=recuperer)


def valider(fichier: Path, reg: Registry, depot_schemas: Path) -> list[str]:
    try:
        doc = json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON invalide : {e}"]
    uri = doc.get("$schema")
    if not uri or not uri.startswith(PREFIXE):
        return ["propriété $schema absente ou inattendue"]
    chemin = depot_schemas / uri[len(PREFIXE) :]
    if not chemin.exists():
        return [f"schéma introuvable dans la copie locale : {uri}"]
    schema = json.loads(chemin.read_text(encoding="utf-8"))
    validateur = Draft7Validator(schema, registry=reg)
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '(racine)'} : {e.message[:300]}"
        for e in sorted(validateur.iter_errors(doc), key=lambda e: list(map(str, e.path)))
    ]


def controles_structure(rapport: Path) -> list[str]:
    """Cohérence entre fichiers : ordre des pages, noms uniques, interactions."""
    erreurs = []
    meta = json.loads((rapport / "pages/pages.json").read_text(encoding="utf-8"))
    dossiers = {p.parent.name for p in (rapport / "pages").glob("*/page.json")}
    if set(meta["pageOrder"]) != dossiers:
        erreurs.append(f"pages.json : pageOrder {meta['pageOrder']} ≠ dossiers {sorted(dossiers)}")
    if meta.get("activePageName") not in dossiers:
        erreurs.append("pages.json : activePageName ne correspond à aucune page")
    for page in sorted((rapport / "pages").glob("*/page.json")):
        doc = json.loads(page.read_text(encoding="utf-8"))
        if doc["name"] != page.parent.name:
            erreurs.append(f"{page} : name ≠ nom du dossier")
        visuels = {}
        for v in sorted(page.parent.glob("visuals/*/visual.json")):
            vd = json.loads(v.read_text(encoding="utf-8"))
            if vd["name"] != v.parent.name:
                erreurs.append(f"{v} : name ≠ nom du dossier")
            visuels[vd["name"]] = vd
            pos = vd["position"]
            if pos["x"] + pos["width"] > doc["width"] or pos["y"] + pos["height"] > doc["height"]:
                erreurs.append(f"{v} : le visuel dépasse de la page")
        for i in doc.get("visualInteractions", []):
            for cle in ("source", "target"):
                if i[cle] not in visuels:
                    erreurs.append(f"{page} : interaction vers un visuel inconnu ({i[cle]})")
    return erreurs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--schemas", type=Path, required=True, help="copie locale de microsoft/json-schemas"
    )
    parser.add_argument("--rapport", type=Path, default=RAPPORT)
    args = parser.parse_args()

    reg = registre(args.schemas)
    nb, erreurs = 0, []
    for fichier in sorted(args.rapport.rglob("*.json")):
        nb += 1
        nom = fichier.relative_to(args.rapport)
        erreurs += [f"{nom} — {m}" for m in valider(fichier, reg, args.schemas)]
    erreurs += controles_structure(args.rapport)

    if erreurs:
        print(f"{len(erreurs)} erreur(s) dans le rapport :")
        print("\n".join(f"  - {e}" for e in erreurs))
        return 1
    print(f"Rapport valide : {nb} fichiers conformes aux schémas Power BI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
