"""Search reviews by meaning, not keywords.  Usage: python src/semantic_search.py "parcel arrived late" """
import sys

import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from db import get_engine
from embed_reviews import MODEL, to_pgvector

# The inner query uses the HNSW index to find the 200 nearest reviews;
# the outer query groups identical texts so each opinion appears once.
SQL = text("""
    WITH nearest AS (
        SELECT stars, review_text, 1 - (embedding <=> CAST(:q AS vector)) AS similarity
        FROM gold.review_embeddings
        ORDER BY embedding <=> CAST(:q AS vector)
        LIMIT 200
    )
    SELECT review_text,
           COUNT(*)                            AS reviews,
           ROUND(AVG(stars), 1)                AS avg_stars,
           ROUND(MAX(similarity)::numeric, 3)  AS similarity
    FROM nearest
    GROUP BY review_text
    ORDER BY similarity DESC
    LIMIT :k""")


def search(query, k=5, model=None, engine=None):
    model = model or SentenceTransformer(MODEL)
    vec = to_pgvector(model.encode(query, normalize_embeddings=True))
    with (engine or get_engine()).connect() as conn:
        return pd.DataFrame(conn.execute(SQL, {"q": vec, "k": k}).mappings().all())


if __name__ == "__main__":
    pd.set_option("display.max_colwidth", 80)
    print(search(" ".join(sys.argv[1:]) or "parcel arrived late"))
