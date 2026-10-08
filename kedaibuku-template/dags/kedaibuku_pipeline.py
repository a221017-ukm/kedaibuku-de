"""KedaiBuku.my daily pipeline: bronze -> silver -> gold."""
import logging
import os
import sys
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task

PROJECT = os.getenv("PROJECT_DIR", "/opt/airflow/project")


def use_project():
    """Run inside the project folder so relative paths like data/lake/... work."""
    os.chdir(PROJECT)
    if f"{PROJECT}/src" not in sys.path:
        sys.path.insert(0, f"{PROJECT}/src")


def alert_on_failure(context):
    ti = context["task_instance"]
    logging.error("ALERT: task %s failed on %s. Log: %s", ti.task_id, context["ds"], ti.log_url)


default_args = {
    "owner": "kedaibuku-data",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": alert_on_failure,
}


@dag(
    dag_id="kedaibuku_pipeline",
    schedule="0 6 * * *",                                   # 6:00 am every day
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kuala_Lumpur"),
    catchup=False,
    default_args=default_args,
    tags=["tttc3213"],
)
def kedaibuku_pipeline():

    @task
    def extract_books():
        use_project()
        import extract_books
        extract_books.run()

    @task
    def extract_fx():
        use_project()
        from extract_fx import extract_fx as fetch
        path, _ = fetch()
        return path

    @task
    def transform_silver():
        use_project()
        import transform_silver
        transform_silver.run()

    @task
    def load_gold():
        use_project()
        import load_gold
        load_gold.run()

    @task
    def check_gold():
        use_project()
        from sqlalchemy import text
        from db import get_engine
        with get_engine().connect() as conn:
            rows = conn.execute(text("SELECT COUNT(*) FROM gold.fact_sales")).scalar()
            negative = conn.execute(text(
                "SELECT COUNT(*) FROM gold.fact_sales WHERE revenue_myr < 0")).scalar()
        if rows == 0 or negative > 0:
            raise ValueError(f"gold check failed: {rows} rows, {negative} negative revenues")
        logging.info("gold.fact_sales OK: %s rows", rows)

    [extract_books(), extract_fx()] >> transform_silver() >> load_gold() >> check_gold()


kedaibuku_pipeline()
