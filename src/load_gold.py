"""Load silver Parquet into PostgreSQL, then build and test the gold star schema with dbt (ELT)."""
import pandas as pd
from sqlalchemy import text

from db import get_engine
from run_dbt import dbt

SILVER = "data/lake/silver"
TABLES = ["books", "customers", "orders", "reviews"]


def load_silver(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
    for table in TABLES:
        df = pd.read_parquet(f"{SILVER}/{table}.parquet")
        df.to_sql(table, engine, schema="silver", if_exists="replace", index=False)
        print(f"silver.{table}: {len(df)} rows")


def run():
    load_silver(get_engine())
    dbt("build")          # builds every gold model, then runs every test


if __name__ == "__main__":
    run()
