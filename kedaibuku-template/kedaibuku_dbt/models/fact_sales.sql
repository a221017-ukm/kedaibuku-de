-- Grain: one order line
select
    o.order_id,
    to_char(o.order_date, 'YYYYMMDD')::int                  as date_key,
    o.customer_id,
    o.book_id,
    o.quantity,
    b.list_price_myr                                        as unit_price_myr,
    round((o.quantity * b.list_price_myr)::numeric, 2)      as revenue_myr
from {{ source('silver', 'orders') }} o
join {{ ref('dim_book') }} b on b.book_id = o.book_id
