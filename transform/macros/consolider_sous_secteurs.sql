{#
  Mécanisme de consolidation (docs/04-modele-dimensions.md, § 3).
  Entrée : une relation avec les colonnes `cles` (dont geo et annee) + sector + valeur_meur +
  valeur_mnac + flags, contenant S13 et les sous-secteurs, zéros compris.
  Sortie : les lignes des sous-secteurs, plus une ligne d'écart par clé :
    - S13_ELIM = S13 − Σ sous-secteurs, quand le pays-année publie ses trois sous-secteurs
      (S1311, S1313, S1314 ; S1312 en plus pour les pays fédéraux) ;
    - _NA      = S13 − Σ sous-secteurs disponibles, sinon (pas d'élimination fictive).
  Une clé présente dans les sous-secteurs mais absente de S13 vaut 0 en S13 : c'est le cas des
  transferts internes, nuls une fois consolidés. La somme des lignes de sortie est donc toujours
  égale à S13.
#}
{% macro consolider_sous_secteurs(relation, cles) %}
  with base as (select * from {{ relation }}),
  completude as (
      select geo, annee,
          count(distinct sector) filter (where sector in ('S1311', 'S1313', 'S1314')) = 3
              as sous_secteurs_complets
      from base
      group by geo, annee
  ),
  s13 as (
      select {{ cles | join(', ') }}, valeur_meur, valeur_mnac, flags
      from base where sector = 'S13'
  ),
  sous as (
      select {{ cles | join(', ') }},
          sum(valeur_meur) as valeur_meur,
          sum(valeur_mnac) as valeur_mnac
      from base
      where sector in ('S1311', 'S1312', 'S1313', 'S1314')
      group by {{ cles | join(', ') }}
  ),
  ecart as (
      select
          {% for c in cles %}coalesce(s13.{{ c }}, sous.{{ c }}) as {{ c }}, {% endfor %}
          coalesce(s13.valeur_meur, 0) - coalesce(sous.valeur_meur, 0) as valeur_meur,
          coalesce(s13.valeur_mnac, 0) - coalesce(sous.valeur_mnac, 0) as valeur_mnac,
          s13.flags
      from s13
      full join sous using ({{ cles | join(', ') }})
  )
  select {{ cles | join(', ') }}, sector, valeur_meur, valeur_mnac, flags
  from base
  where sector in ('S1311', 'S1312', 'S1313', 'S1314')
      and (abs(valeur_meur) > 0.05 or abs(coalesce(valeur_mnac, 0)) > 0.05)
  union all
  select {% for c in cles %}e.{{ c }}, {% endfor %}
      case when c.sous_secteurs_complets then 'S13_ELIM' else '_NA' end as sector,
      e.valeur_meur, e.valeur_mnac, e.flags
  from ecart as e
  join completude as c using (geo, annee)
  where abs(e.valeur_meur) > 0.05 or abs(coalesce(e.valeur_mnac, 0)) > 0.05
{% endmacro %}
