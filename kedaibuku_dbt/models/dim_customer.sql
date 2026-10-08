-- No direct identifiers reach gold
select customer_id, state, age_group, email_missing, signup_date::date as signup_date
from {{ source('silver', 'customers') }}
