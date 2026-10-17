select * from {{ ref('ref_cofog') }}
union all
select '_NA', '_NA', 'Non renseigné', '_NA', 'Non renseigné', 2, true, 99999
