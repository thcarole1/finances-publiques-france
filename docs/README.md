# Spécification — sommaire

> **Statut : proposition v0.1, à valider par pull request.**
> Aucun code n'est écrit avant validation de cette spécification.
> Les points qui demandent ton arbitrage sont regroupés dans [`11-decisions-ouvertes.md`](11-decisions-ouvertes.md).

| # | Document | Contenu |
|---|---|---|
| 01 | [Cadrage](01-cadrage.md) | Objectifs, périmètre, choix de conception, principes directeurs |
| 02 | [Architecture](02-architecture.md) | Pipeline, couches de données, stockage, outillage, organisation du dépôt |
| 03 | [Sources et licences](03-sources-et-licences.md) | Catalogue des sources, jeux de données, fréquence, licence, lot |
| 04 | [Modèle — dimensions](04-modele-dimensions.md) | Dimensions conformes, clés, attributs, hiérarchies |
| 05 | [Modèle — faits](05-modele-faits.md) | Tables de faits, grains, clés, additivité, relations |
| 06 | [Mesures et calculs](06-mesures-dax.md) | Mesures DAX principales, groupes de calcul, paramètres de champ |
| 07 | [Qualité des données](07-qualite-donnees.md) | Contrôles bloquants et avertissements, identités comptables |
| 08 | [Scénarios et projections](08-scenarios-projections.md) | Hypothèses, moteur de projection, bibliothèque de scénarios |
| 09 | [Rapport](09-rapport.md) | Parcours guidé, pages d'exploration, couche pédagogique |
| 10 | [Conventions](10-conventions.md) | Nommage, Git, versions, unités, documentation |
| 11 | [Décisions ouvertes](11-decisions-ouvertes.md) | Points à arbitrer avant le lot 1 |
| — | [Glossaire](glossaire.md) | Notions clés (alimente aussi la table `Dim_Glossaire` du modèle) |

## Comment relire

1. Lire `01-cadrage.md` pour vérifier que tes choix sont fidèlement retranscrits.
2. Parcourir `05-modele-faits.md` : c'est le cœur du modèle.
3. Répondre aux questions de `11-decisions-ouvertes.md`, en commentaire de la pull request.

Le reste peut être lu en diagonale à ce stade : ces documents serviront de référence pendant
la construction et seront mis à jour à chaque lot.

## Niveaux de confiance

Certains éléments (codes exacts de jeux de données, disponibilité d'un détail pour un pays…)
seront confirmés lors de l'exploration des sources au lot concerné. Ils sont signalés par
**[À confirmer]**.
