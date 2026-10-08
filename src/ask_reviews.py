"""Retrieval-augmented generation (RAG): answer a question using only the most relevant reviews.

Needs a local LLM:  docker run -d -p 11434:11434 --name ollama ollama/ollama
                    docker exec ollama ollama pull qwen2.5:1.5b
Usage: python src/ask_reviews.py "What do customers complain about most?"
"""
import sys

import requests

from semantic_search import search

PROMPT = """You are a data analyst at KedaiBuku.my, a Malaysian online bookstore.
Answer the question using ONLY the customer reviews below. Reviews may be in English or Malay.
Answer in English, in at most three sentences. If the reviews do not answer the question, say so.

Reviews:
{context}

Question: {question}"""


def ask(question, k=8):
    hits = search(question, k=k)                                   # 1. retrieve
    context = "\n".join(f"- {row.review_text} ({row.reviews} customers, average {row.avg_stars} stars)"
                        for row in hits.itertuples())
    response = requests.post("http://localhost:11434/api/generate", timeout=180, json={
        "model": "qwen2.5:1.5b",
        "prompt": PROMPT.format(context=context, question=question),  # 2. augment
        "stream": False,
    })
    response.raise_for_status()
    return response.json()["response"], hits                          # 3. generate


if __name__ == "__main__":
    answer, sources = ask(" ".join(sys.argv[1:]) or "What do customers complain about most?")
    print(answer)
    print("\nBased on these reviews:")
    print(sources.to_string(index=False))
