-- Dernier instantané de gov_10q_ggdebt : dette de Maastricht en fin de trimestre, par sous-secteur.
select * from (
    {{ lire_eurostat('gov_10q_ggdebt', ['na_item', 'sector', 'unit']) }}
)
where annee >= 1995 and na_item = 'GD'
