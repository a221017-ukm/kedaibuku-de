"""Embed reviews with a multilingual model, store the vectors in pgvector, and tag each review's topic."""
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from db import get_engine

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"   # 384 dimensions, English + Malay
DIM = 384

# Zero-shot topic tagging: describe each topic in a few phrases (both languages); no training data needed
ASPECTS = {
    "delivery":  ["delivery was slow or fast", "the parcel arrived late", "shipping time", "penghantaran lambat"],
    "packaging": ["the book arrived damaged", "torn cover, bent pages", "well packed box", "bungkusan rosak"],
    "price":     ["the price is too expensive", "good value for money", "cheap price", "harga mahal"],
    "content":   ["the story and writing quality", "boring plot", "well written book", "jalan cerita menarik"],
    "service":   ["customer service and seller response", "no reply to my refund request", "helpful seller",
                  "penjual tidak membalas"],
}


def to_pgvector(vec):
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def prototype(model, phrases):
    """Average the phrase vectors into one topic vector, rescaled to length 1."""
    mean = model.encode(phrases, normalize_embeddings=True).mean(axis=0)
    return mean / np.linalg.norm(mean)


def run():
    engine = get_engine()
    model = SentenceTransformer(MODEL)

    reviews = pd.read_parquet("data/lake/silver/reviews.parquet")
    reviews = reviews[reviews["has_text"]].copy()
    vectors = model.encode(reviews["review_text"].tolist(), batch_size=64,
                           normalize_embeddings=True, show_progress_bar=True)

    reviews["date_key"] = reviews["review_date"].dt.strftime("%Y%m%d").astype(int)
    reviews["embedding"] = [to_pgvector(v) for v in vectors]
    reviews["model_name"] = MODEL
    reviews["embedded_at"] = datetime.now(timezone.utc)
    cols = ["review_id", "date_key", "customer_id", "book_id", "stars", "review_text",
            "embedding", "model_name", "embedded_at"]

    prototypes = pd.DataFrame({
        "aspect": list(ASPECTS),
        "embedding": [to_pgvector(prototype(model, phrases)) for phrases in ASPECTS.values()],
    })

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold"))
        conn.execute(text("DROP TABLE IF EXISTS gold.fact_reviews, gold.review_embeddings, gold.aspect_prototypes"))
    reviews[cols].to_sql("review_embeddings", engine, schema="gold", if_exists="replace", index=False)
    prototypes.to_sql("aspect_prototypes", engine, schema="gold", if_exists="replace", index=False)

    with engine.begin() as conn:
        for table in ["review_embeddings", "aspect_prototypes"]:
            conn.execute(text(f"ALTER TABLE gold.{table} ALTER COLUMN embedding "
                              f"TYPE vector({DIM}) USING embedding::vector"))
        conn.execute(text("CREATE INDEX ON gold.review_embeddings "
                          "USING hnsw (embedding vector_cosine_ops)"))
        # Tag every review with its nearest topic, entirely in SQL
        conn.execute(text("""
            CREATE TABLE gold.fact_reviews AS
            SELECT r.review_id, r.date_key, r.customer_id, r.book_id, r.stars,
                   a.aspect,
                   ROUND((1 - (r.embedding <=> a.embedding))::numeric, 3) AS aspect_similarity,
                   r.model_name, r.embedded_at
            FROM gold.review_embeddings r
            CROSS JOIN LATERAL (
                SELECT p.aspect, p.embedding
                FROM gold.aspect_prototypes p
                ORDER BY r.embedding <=> p.embedding
                LIMIT 1
            ) a"""))
        counts = conn.execute(text(
            "SELECT aspect, COUNT(*) FROM gold.fact_reviews GROUP BY aspect ORDER BY 2 DESC")).all()

    run_info = {"model": MODEL, "rows_embedded": len(reviews), "aspects": dict(counts),
                "embedded_at": reviews["embedded_at"].iloc[0].isoformat()}
    os.makedirs("data/lake/gold", exist_ok=True)
    with open("data/lake/gold/model_runs.jsonl", "a") as f:
        f.write(json.dumps(run_info) + "\n")
    print(run_info)


if __name__ == "__main__":
    run()
