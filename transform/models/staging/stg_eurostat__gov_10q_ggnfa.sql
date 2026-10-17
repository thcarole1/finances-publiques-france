-- Dernier instantané de gov_10q_ggnfa : dépenses, recettes, solde et intérêts trimestriels (S13).
select * from (
    {{ lire_eurostat('gov_10q_ggnfa', ['unit', 's_adj', 'sector', 'na_item']) }}
)
where annee >= 1995 and sector = 'S13'
