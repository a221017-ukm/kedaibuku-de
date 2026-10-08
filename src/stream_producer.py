"""Simulate KedaiBuku's web shop: send each new order to Kafka as a live event.

Usage: python src/stream_producer.py 200        (sends 200 orders, about 2 per second)
"""
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
from confluent_kafka import Producer

TOPIC = "orders"


def delivered(err, msg):
    if err:
        print("delivery failed:", err)


def run(n=200, delay=0.5):
    books = pd.read_parquet("data/lake/silver/books.parquet")[["book_id", "category", "price_myr"]]
    customers = pd.read_parquet("data/lake/silver/customers.parquet")["customer_id"].tolist()
    producer = Producer({"bootstrap.servers": "localhost:9092"})

    for i in range(1, n + 1):
        book = books.sample(1).iloc[0]
        event = {
            "order_id": "S" + uuid.uuid4().hex[:10],       # unique across every run
            "customer_id": random.choice(customers),
            "book_id": book["book_id"],
            "category": book["category"],
            "quantity": random.choice([1, 1, 1, 2, 3]),
            "price_myr": float(book["price_myr"]),
            "event_time": datetime.now(timezone.utc).isoformat(),
        }
        # The key decides the partition: all orders from one customer stay in order
        producer.produce(TOPIC, key=event["customer_id"], value=json.dumps(event), on_delivery=delivered)
        producer.poll(0)
        if i % 20 == 0:
            print(f"sent {i} orders")
        time.sleep(delay)
    producer.flush()


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
