-- Rôle « receveur » de Dim_Sous_Secteur, pour Fait_Transferts_APU (relations simples et actives).
select * from {{ ref('dim_sous_secteur') }}
where not est_elimination
