#!/usr/bin/env bash
# Construit les tables du modèle : seeds (référentiels) → modèles → tests → export Parquet.
# À lancer depuis la racine du dépôt :  ./scripts/construire.sh
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p data/staging data/curated
uv run dbt build --project-dir transform --profiles-dir transform "$@"
