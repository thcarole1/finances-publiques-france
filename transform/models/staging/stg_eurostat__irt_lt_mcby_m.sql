-- Dernier instantané de irt_lt_mcby_m : taux des emprunts d'État à 10 ans (critère de
-- convergence de Maastricht), moyenne mensuelle, en %.
select * from (
    {{ lire_eurostat('irt_lt_mcby_m', ['int_rt']) }}
)
where annee >= 1995 and int_rt = 'MCBY' and valeur is not null
