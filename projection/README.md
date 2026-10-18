# Moteur de projection de la dette

- `moteur.py` : projection année par année avec refinancement (docs/08, § 3 b).
- `scenarios.py` : situation de départ, scénarios de base (`TENDANCIEL`, gouvernement) et
  scénarios personnels (`scenarios/*.yml`).

Appelé par le modèle dbt `transform/models/marts/fait_projections.py` à chaque construction.
Tests : `tests/test_projection.py` (dont le contrôle croisé avec la formule du laboratoire DAX).
