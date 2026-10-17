# 11 — Décisions

> **Statut : toutes les décisions sont arrêtées (17/10/2026, commentaire de la PR #1).**
> Les options écartées restent listées ci-dessous pour garder la trace du raisonnement.

| # | Sujet | Décision |
|---|---|---|
| D1 | Outil de transformation | **dbt avec DuckDB** |
| D2 | Millésimes dans Power BI | **Dernier millésime partout + historique pour les agrégats clés et les prévisions** |
| D3 | Licence du code | **MIT** |
| D4 | Pays OCDE hors UE | **États-Unis, Royaume-Uni, Japon, Canada, Suisse, Norvège, Australie, Corée du Sud** |
| D5 | Source des fichiers Power BI | **Local ou en ligne, au choix par paramètre** |
| D6 | Profondeur des collectivités | **Toute la profondeur disponible** (volume à confirmer au lot 7) |
| D7 | Noms des colonnes | **`snake_case` + noms d'affichage en français** |
| D8 | Visibilité du dépôt | **Public** |
| D9 | Profondeur du trimestriel | **Depuis 2000** |
| D10 | Protection de `main` | **Activée** (configuration au lot 0) |
| D11 | Convention d'incidence économique | **Fournie par défaut, sourcée et modifiable** |

Toute décision peut être rouverte plus tard par une PR qui modifie ce fichier.

---

### D1 — Outil de transformation

**✅ Décision : A**

- **A.** **dbt avec DuckDB** : transformations en SQL, tests et documentation intégrés, contrôles
  qualité natifs. *(Recommandé : tu connais déjà dbt, et les tests dbt couvrent la plupart des
  contrôles de `07`.)*
- **B.** Python seul (`polars`) : un seul langage, mais les tests et la documentation sont à
  construire.
- **C.** Scripts SQL DuckDB sans dbt : léger, mais sans gestion des dépendances ni des tests.
- **D.** Autre.

### D2 — Chargement des millésimes dans Power BI

**✅ Décision : A**

- **A.** **Dernier millésime pour tous les faits + tous les millésimes pour les agrégats clés
  (`Fait_Revisions`) et les prévisions (`Fait_Hypotheses`)**. *(Recommandé : volume maîtrisé.)*
- **B.** Tous les millésimes dans tous les faits : analyse de révision partout, mais volume
  multiplié et mesures plus complexes (filtre de millésime obligatoire partout).
- **C.** Autre.

### D3 — Licence du code

**✅ Décision : A**

Les données restent sous la licence de leurs producteurs (voir `03`).

- **A.** **MIT** : très permissive, la plus courante. *(Recommandé.)*
- **B.** Apache 2.0 : permissive, avec clause sur les brevets.
- **C.** Pas de licence : tous droits réservés, ce qui limite la réutilisation par d'autres.
- **D.** Autre.

### D4 — Pays de l'OCDE hors UE (lot 8)

**✅ Décision : A**

- **A.** **États-Unis, Royaume-Uni, Japon, Canada, Suisse, Norvège, Australie, Corée du Sud.**
  *(Recommandé : grandes économies + modèles sociaux contrastés.)*
- **B.** Pays du G7 hors UE seulement (États-Unis, Royaume-Uni, Japon, Canada).
- **C.** Tous les pays de l'OCDE.
- **D.** Autre.

### D5 — Source des fichiers pour Power BI

**✅ Décision : A**

- **A.** **Les deux modes, au choix par un paramètre** : dossier local (clone) ou fichiers en ligne
  du dépôt. *(Recommandé.)*
- **B.** Dossier local seulement.
- **C.** En ligne seulement.
- **D.** Autre.

### D6 — Profondeur historique des collectivités (lot 7)

**✅ Décision : A**

- **A.** **Toute la profondeur disponible** dans les jeux OFGL et REI. *(Recommandé, volume à
  confirmer au lot 7.)*
- **B.** Depuis 2017 (périmètre intercommunal stabilisé après la loi NOTRe).
- **C.** Autre.

### D7 — Noms des colonnes dans le modèle

**✅ Décision : A**

- **A.** **`snake_case` dans les fichiers et le modèle, avec des noms d'affichage en français**
  pour le rapport. *(Recommandé : robuste pour le code, lisible pour l'utilisateur.)*
- **B.** Noms en français avec espaces et accents directement dans le modèle.
- **C.** Autre.

### D8 — Visibilité du dépôt

**✅ Décision : A**

- **A.** **Public** : minutes GitHub Actions illimitées, protection de branche gratuite,
  actualisation possible depuis le service Power BI. *(Recommandé.)*
- **B.** Privé.
- **C.** Autre.

### D9 — Profondeur du trimestriel

**✅ Décision : A**

- **A.** **Depuis 2000** : couvre 2008, la crise de la zone euro, le Covid et l'inflation.
  *(Recommandé.)*
- **B.** Depuis 2015.
- **C.** Autre.

### D10 — Protection de la branche `main`

**✅ Décision : A**

- **A.** **Activée** : fusion uniquement par PR, contrôles CI obligatoires. Tu la configures dans
  les paramètres du dépôt (je te guiderai au lot 0). *(Recommandé ; gratuit si le dépôt est public.)*
- **B.** Non activée.
- **C.** Autre.

### D11 — Convention d'incidence « économique » (qui supporte vraiment l'impôt)

**✅ Décision : A**

- **A.** **Fournir une convention économique par défaut**, fondée sur des hypothèses courantes de
  la littérature (ex. cotisations employeurs supportées majoritairement par les salariés à long
  terme), chaque coefficient étant sourcé et modifiable. *(Recommandé : très parlant, mais
  clairement présenté comme une hypothèse.)*
- **B.** Convention légale seulement.
- **C.** Autre.
