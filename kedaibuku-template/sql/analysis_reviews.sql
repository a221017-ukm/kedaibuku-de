-- 1. Which topics drive low ratings in each category?
SELECT b.category, r.aspect,
       COUNT(*)                                    AS reviews,
       ROUND(AVG(r.stars), 2)                      AS avg_stars,
       ROUND(AVG((r.stars <= 2)::int) * 100, 1)    AS pct_low_rating
FROM gold.fact_reviews r
JOIN gold.dim_book b USING (book_id)
GROUP BY b.category, r.aspect
HAVING COUNT(*) >= 10
ORDER BY pct_low_rating DESC
LIMIT 10;

-- 2. OLAP roll-up: revenue by quarter and month, with subtotals and a grand total
SELECT d.quarter, d.month, SUM(f.revenue_myr) AS revenue_myr
FROM gold.fact_sales f JOIN gold.dim_date d USING (date_key)
GROUP BY ROLLUP (d.quarter, d.month)
ORDER BY d.quarter NULLS LAST, d.month NULLS LAST;

-- 3. Evaluate the AI: a random sample to label by hand
SELECT e.review_id, e.review_text, r.aspect, r.aspect_similarity
FROM gold.fact_reviews r
JOIN gold.review_embeddings e USING (review_id)
ORDER BY random()
LIMIT 20;
