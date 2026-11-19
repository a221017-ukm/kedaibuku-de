
import os
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import text

from db import get_engine

# Connect to PostgreSQL
engine = get_engine()

# Create output folder
os.makedirs("reports/graphs", exist_ok=True)

# 1. Monthly Sales Trend
monthly_sales = pd.read_sql_query(text("""
    SELECT
        d.year,
        d.month,
        d.month_name,
        SUM(f.revenue_myr) AS revenue
    FROM gold.fact_sales f
    JOIN gold.dim_date d ON f.date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
    ORDER BY d.year, d.month
"""), engine)

plt.figure(figsize=(10, 5))
plt.plot(
    monthly_sales["month_name"] + " " + monthly_sales["year"].astype(str),
    monthly_sales["revenue"],
    marker="o"
)
plt.title("Monthly Sales Trend")
plt.xlabel("Month")
plt.ylabel("Revenue (MYR)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("reports/graphs/monthly_sales.png", dpi=300)
plt.close()

# 2. Top 10 Bestselling Books
top_books = pd.read_sql_query(text("""
    SELECT
        b.title,
        SUM(f.quantity) AS total_sold
    FROM gold.fact_sales f
    JOIN gold.dim_book b ON f.book_id = b.book_id
    GROUP BY b.title
    ORDER BY total_sold DESC
    LIMIT 10
"""), engine)

plt.figure(figsize=(10, 6))
plt.barh(top_books["title"], top_books["total_sold"])
plt.title("Top 10 Bestselling Books")
plt.xlabel("Quantity Sold")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("reports/graphs/top_books.png", dpi=300)
plt.close()

# 3. Sales by Malaysian State
state_sales = pd.read_sql_query(text("""
    SELECT
        c.state,
        SUM(f.revenue_myr) AS revenue
    FROM gold.fact_sales f
    JOIN gold.dim_customer c ON f.customer_id = c.customer_id
    GROUP BY c.state
    ORDER BY revenue DESC
"""), engine)

plt.figure(figsize=(10, 6))
plt.bar(state_sales["state"], state_sales["revenue"])
plt.title("Sales Revenue by State")
plt.xlabel("State")
plt.ylabel("Revenue (MYR)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("reports/graphs/sales_by_state.png", dpi=300)
plt.close()

# 4. Revenue by Book Category
category_sales = pd.read_sql_query(text("""
    SELECT
        b.category,
        SUM(f.revenue_myr) AS revenue
    FROM gold.fact_sales f
    JOIN gold.dim_book b ON f.book_id = b.book_id
    GROUP BY b.category
    ORDER BY revenue DESC
"""), engine)

plt.figure(figsize=(9, 6))
plt.bar(category_sales["category"], category_sales["revenue"])
plt.title("Revenue by Book Category")
plt.xlabel("Book Category")
plt.ylabel("Revenue (MYR)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("reports/graphs/revenue_by_category.png", dpi=300)
plt.close()

print("All 4 graphs generated successfully!")
print("Location: reports/graphs/")
