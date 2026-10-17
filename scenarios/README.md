# Scénarios personnels

Un fichier YAML par scénario. Chaque modification passe par une pull request : l'historique
Git est l'historique de tes scénarios.

- Format et règles : `docs/08-scenarios-projections.md` (§ 4).
- Schéma de validation : `_schema.json`, vérifié en CI par `scripts/valider_scenarios.py`.
- Point de départ : dupliquer `exemple-choc-de-taux.yml`.

L'existence du scénario de base (`base`) dans `Dim_Scenario` sera vérifiée à partir du lot 4.
