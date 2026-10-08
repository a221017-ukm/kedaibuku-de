"""Run dbt with the credentials from .env.

Usage from the project root:  python src/run_dbt.py build   (or debug, test, docs generate ...)
"""
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()


def dbt(*args):
    cmd = [os.getenv("DBT_BIN", "dbt"), *args,
           "--project-dir", "kedaibuku_dbt", "--profiles-dir", "kedaibuku_dbt"]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"dbt {' '.join(args)} failed")


if __name__ == "__main__":
    dbt(*sys.argv[1:])
