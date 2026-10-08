"""Lab 3: fetch today's GBP-to-MYR exchange rate from the Bank Negara Malaysia Open API.

Run from the project folder:  python src/extract_fx.py
"""
import json
import os
from datetime import date

import requests

URL = "https://api.bnm.gov.my/public/exchange-rate/GBP"
HEADERS = {"Accept": "application/vnd.BNM.API.v1+json"}   # the BNM API requires this header


def extract_fx():
    os.makedirs("data/lake/bronze", exist_ok=True)
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    payload = response.json()
    path = f"data/lake/bronze/fx_gbp_{date.today():%Y%m%d}.json"   # one new file per day
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path, payload


if __name__ == "__main__":
    path, payload = extract_fx()
    print("Saved", path)
    print(json.dumps(payload["data"], indent=2))
