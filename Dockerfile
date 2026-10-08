# Lab 7, Step 2: Airflow image with the packages the pipeline needs
FROM apache/airflow:2.10.5-python3.11
COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt"

# dbt lives in its own environment so its packages never clash with Airflow's
USER root
RUN python -m venv /opt/dbt_venv && /opt/dbt_venv/bin/pip install --no-cache-dir dbt-postgres
USER airflow
ENV DBT_BIN=/opt/dbt_venv/bin/dbt
