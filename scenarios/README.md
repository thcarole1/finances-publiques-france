# Scénarios personnels

Un fichier YAML par scénario. Chaque modification passe par une pull request : l'historique
Git est l'historique de tes scénarios.

- Format et règles : `docs/08-scenarios-projections.md` (§ 4).
- Schéma de validation : `_schema.json`, vérifié en CI par `scripts/valider_scenarios.py`.
- Point de départ : dupliquer `exemple-choc-de-taux.yml`.

Scénarios de base disponibles (`base`) :

- `TENDANCIEL` : croissance 1 %, inflation 1,8 %, taux à 10 ans et solde hors intérêts de la
  dernière année connue, maintenus ;
- `GOUV_PLF_2027` : dernière trajectoire du gouvernement (croissance et solde public annoncés pour
  2026 et 2027), puis solde hors intérêts maintenu.

Les projections sont recalculées à chaque construction (`transform/models/marts/fait_projections.py`,
moteur `projection/`) et s'affichent sur la page « Mes scénarios » du rapport.
