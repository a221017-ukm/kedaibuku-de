-- Lab 6: questions answered from the gold star schema

-- 1. Monthly revenue by category
SELECT d.month, d.month_name, b.category, SUM(f.revenue_myr) AS revenue_myr
FROM gold.fact_sales f
JOIN gold.dim_date d USING (date_key)
JOIN gold.dim_book b USING (book_id)
GROUP BY d.month, d.month_name, b.category
ORDER BY d.month, revenue_myr DESC;

-- 2. Top 3 books per category
WITH book_rev AS (
    SELECT b.category, b.title, SUM(f.revenue_myr) AS revenue_myr,
           RANK() OVER (PARTITION BY b.category ORDER BY SUM(f.revenue_myr) DESC) AS rnk
    FROM gold.fact_sales f JOIN gold.dim_book b USING (book_id)
    GROUP BY b.category, b.title
)
SELECT category, title, revenue_myr, rnk FROM book_rev WHERE rnk <= 3 ORDER BY category, rnk;

-- 3. Revenue per customer by state and age group
SELECT c.state, c.age_group, COUNT(DISTINCT f.customer_id) AS customers,
       ROUND(SUM(f.revenue_myr) / COUNT(DISTINCT f.customer_id), 2) AS revenue_per_customer
FROM gold.fact_sales f JOIN gold.dim_customer c USING (customer_id)
GROUP BY c.state, c.age_group
ORDER BY revenue_per_customer DESC;
