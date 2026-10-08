"""Land bronze files in S3-compatible object storage, the way cloud data lakes store raw data."""
import io
import os
from datetime import date
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.getenv("S3_BUCKET", "kedaibuku-lake")


def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name="us-east-1",          # required by the SDK; ignored by the local server
    )


def upload_bronze(s3, ingest_date=None):
    """Copy every bronze file to s3://<bucket>/bronze/ingest_date=YYYY-MM-DD/<file>."""
    ingest_date = ingest_date or date.today().isoformat()
    existing = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if BUCKET not in existing:
        s3.create_bucket(Bucket=BUCKET)
    for path in sorted(Path("data/lake/bronze").glob("*")):
        key = f"bronze/ingest_date={ingest_date}/{path.name}"
        s3.upload_file(str(path), BUCKET, key)
        print("uploaded", key)


def read_csv_from_lake(s3, key):
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    return pd.read_csv(io.BytesIO(body))


def run():
    s3 = get_s3()
    upload_bronze(s3)
    for obj in s3.list_objects_v2(Bucket=BUCKET, Prefix="bronze/")["Contents"]:
        print(f"{obj['Size']:>10,}  {obj['Key']}")


if __name__ == "__main__":
    run()
