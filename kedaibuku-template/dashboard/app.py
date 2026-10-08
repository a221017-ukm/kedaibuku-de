"""KedaiBuku.my dashboard. Run from the project root: streamlit run dashboard/app.py"""
import sys

import pandas as pd
import streamlit as st

sys.path.append("src")
from db import get_engine  # noqa: E402

st.set_page_config(page_title="KedaiBuku.my", layout="wide")


@st.cache_data(ttl=600)
def query(sql):
    return pd.read_sql(sql, get_engine())


@st.cache_resource
def load_model():
    from sentence_transformers import SentenceTransformer
    from embed_reviews import MODEL
    return SentenceTransformer(MODEL)


categories = query("SELECT DISTINCT category FROM gold.dim_book ORDER BY 1")["category"].tolist()
chosen = st.sidebar.multiselect("Category", categories, default=categories)
if not chosen:
    st.warning("Pick at least one category.")
    st.stop()
in_list = ", ".join("'" + c.replace("'", "''") + "'" for c in chosen)

sales = query(f"""
    SELECT d.month, b.category, f.customer_id, f.revenue_myr
    FROM gold.fact_sales f
    JOIN gold.dim_date d USING (date_key)
    JOIN gold.dim_book b USING (book_id)
    WHERE b.category IN ({in_list})""")
reviews = query(f"""
    SELECT b.category, r.aspect, r.stars
    FROM gold.fact_reviews r JOIN gold.dim_book b USING (book_id)
    WHERE b.category IN ({in_list})""")

st.title("KedaiBuku.my sales and customer voice")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue (RM)", f"{sales['revenue_myr'].sum():,.0f}")
k2.metric("Orders", f"{len(sales):,}")
k3.metric("Customers", f"{sales['customer_id'].nunique():,}")
k4.metric("Average review", f"{reviews['stars'].mean():.2f} stars")

left, right = st.columns(2)
left.subheader("Revenue by month (RM)")
left.bar_chart(sales.groupby("month", as_index=False)["revenue_myr"].sum(), x="month", y="revenue_myr")

topics = (reviews.groupby("aspect")
                 .agg(reviews=("stars", "size"), avg_stars=("stars", "mean"))
                 .round(2).sort_values("reviews", ascending=False).reset_index())
right.subheader("What customers talk about (AI-tagged topics)")
right.bar_chart(topics, x="aspect", y="reviews")
right.dataframe(topics, hide_index=True)

st.subheader("Ask the reviews (semantic search, English or Malay)")
question = st.text_input("Search by meaning", placeholder="e.g. parcel arrived late, harga mahal")
if question:
    from semantic_search import search
    st.dataframe(search(question, k=8, model=load_model()), hide_index=True)
