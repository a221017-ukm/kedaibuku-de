"""Read live orders from Kafka, keep running revenue by category, and land micro-batches in the bronze bucket.

Usage: python src/stream_consumer.py
"""
import json
import time
from collections import defaultdict
from datetime import datetime, timezone

from confluent_kafka import Consumer

from lake import BUCKET, get_s3

BATCH_SIZE, BATCH_SECONDS = 20, 10


def show_assignment(consumer, partitions):
    print("assigned partitions:", sorted(p.partition for p in partitions))


def land_batch(s3, batch):
    now = datetime.now(timezone.utc)
    key = f"bronze/stream/orders/date={now:%Y-%m-%d}/batch-{now:%H%M%S%f}.jsonl"
    s3.put_object(Bucket=BUCKET, Key=key, Body="\n".join(json.dumps(e) for e in batch).encode())
    return key


def run(max_messages=None):
    s3 = get_s3()
    if BUCKET not in [b["Name"] for b in s3.list_buckets().get("Buckets", [])]:
        s3.create_bucket(Bucket=BUCKET)
    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "kedai-revenue",          # consumers in one group share the partitions
        "auto.offset.reset": "earliest",      # a brand-new group starts from the oldest event
        "enable.auto.commit": False,          # we commit only after the batch is safely landed
    })
    consumer.subscribe(["orders"], on_assign=show_assignment)

    revenue, batch, seen, last_flush = defaultdict(float), [], 0, time.time()
    try:
        while max_messages is None or seen < max_messages:
            msg = consumer.poll(1.0)
            if msg is not None and not msg.error():
                event = json.loads(msg.value())
                revenue[event["category"]] += event["quantity"] * event["price_myr"]
                batch.append(event)
                seen += 1
            if batch and (len(batch) >= BATCH_SIZE or time.time() - last_flush > BATCH_SECONDS):
                key = land_batch(s3, batch)
                consumer.commit(asynchronous=False)       # at-least-once: land first, then commit
                top = sorted(revenue.items(), key=lambda kv: -kv[1])[:3]
                print(f"{seen} orders | landed {key} | top: " +
                      ", ".join(f"{c} RM{v:,.0f}" for c, v in top))
                batch, last_flush = [], time.time()
    except KeyboardInterrupt:
        pass
    finally:
        if batch:                                         # land what is left before stopping
            land_batch(s3, batch)
            consumer.commit(asynchronous=False)
        consumer.close()


if __name__ == "__main__":
    run()
