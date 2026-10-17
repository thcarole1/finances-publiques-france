# Référentiels

Nomenclatures et correspondances **maintenues à la main**, relues en pull request.
Ce sont, avec les instantanés bruts, les seules sources de vérité du projet.

Chargés comme *seeds* dbt (`seed-paths` de `transform/dbt_project.yml`) ; leur schéma et
leurs tests sont déclarés dans `_seeds.yml`.

| Fichier | Contenu | Lot |
|---|---|---|
| `ref_sous_secteur.csv` | Sous-secteurs des APU et ligne d'élimination | 0 |
| `ref_periodes_historiques.csv` | Repères de crises pour les graphiques | 0 |
| `ref_pays.csv` | Pays, agrégats, correspondances de codes, comparabilité | 1 |
| `ref_transaction.csv` | Feuilles de nature (SEC 2010) | 1 |
| `ref_formule_comptes_apu.csv` | Calcul de chaque feuille à partir de `gov_10a_main` | 1 |
| `ref_formule_depense_fonction.csv` | Correspondance des natures de `gov_10a_exp` | 1 |
| `ref_cofog.csv` | Fonctions COFOG et résidus non ventilés | 1 |
| `ref_prelevement.csv` | Types de prélèvement | 1 |
| `ref_formule_prelevement.csv` | Calcul de chaque prélèvement, résidus compris | 1 |
| `ref_source.csv` | Sources, licences, attributions | 1 |
| `ref_indicateur.csv` | Indicateurs suivis | 1 |
