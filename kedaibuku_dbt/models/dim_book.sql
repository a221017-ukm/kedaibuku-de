select book_id, title, category, price_myr as list_price_myr, rating, in_stock
from {{ source('silver', 'books') }}
