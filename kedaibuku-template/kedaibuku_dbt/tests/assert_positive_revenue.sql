-- A singular test: returns the rows that break the rule. Zero rows = pass.
select order_id, quantity, revenue_myr
from {{ ref('fact_sales') }}
where revenue_myr <= 0 or quantity <= 0
