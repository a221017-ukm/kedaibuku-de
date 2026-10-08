"""Bronze -> silver: clean, validate and mask personal data."""
import glob
import hashlib
import json
import os
import re

import pandas as pd
from dotenv import load_dotenv

from quality import (assert_between, assert_foreign_key, assert_min_rows,
                     assert_not_null, assert_unique, expect)

load_dotenv()
BRONZE, SILVER = "data/lake/bronze", "data/lake/silver"
SALT = os.getenv("PII_SALT", "change-me")

STATE_MAP = {"selangor": "Selangor", "sgr": "Selangor", "kl": "WP Kuala Lumpur",
             "kuala lumpur": "WP Kuala Lumpur", "penang": "Pulau Pinang",
             "p. pinang": "Pulau Pinang", "johor": "Johor", "jhr": "Johor"}
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PHONE_RE = re.compile(r"\+?6?01\d-?\d{7,8}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


# ---------- helpers ----------
def hash_value(value):
    """One-way pseudonym: same input -> same hash, but cannot be reversed without the salt."""
    if pd.isna(value):
        return None
    return hashlib.sha256((SALT + str(value).lower()).encode()).hexdigest()[:16]


def mask_email(email):
    if pd.isna(email):
        return None
    user, domain = email.split("@", 1)
    return f"{user[0]}***@{domain}"


def redact_text(text):
    if pd.isna(text):
        return None
    return EMAIL_RE.sub("[EMAIL]", PHONE_RE.sub("[PHONE]", text))


def birth_year_from_mykad(mykad):
    yy = int(str(mykad)[:2])
    return 1900 + yy if yy > 26 else 2000 + yy


# ---------- tables ----------
def latest_fx_rate():
    latest = sorted(glob.glob(f"{BRONZE}/fx_gbp_*.json"))[-1]
    with open(latest) as f:
        rate = json.load(f)["data"]["rate"]
    return rate["middle_rate"], rate["date"]


def clean_books():
    b = pd.read_csv(f"{BRONZE}/books.csv").drop_duplicates("book_id")
    rate, rate_date = latest_fx_rate()
    b["price_gbp"] = b["price_raw"].str.replace(r"[^0-9.]", "", regex=True).astype(float)
    b["price_myr"] = (b["price_gbp"] * rate).round(2)
    b["fx_rate_date"] = pd.to_datetime(rate_date)
    b["rating"] = b["rating_raw"].map(RATING).astype("Int64")
    b["in_stock"] = b["availability"].str.contains("In stock", na=False)
    b = b[["book_id", "title", "category", "price_gbp", "price_myr", "fx_rate_date", "rating", "in_stock"]]

    assert_min_rows(b, 900, "books")
    assert_unique(b, "book_id", "books")
    assert_not_null(b, "rating", "books")
    assert_between(b, "price_gbp", 0.01, 500, "books")
    return b


def clean_customers():
    c = pd.read_csv(f"{BRONZE}/customers.csv").drop_duplicates()
    c["state"] = c["state"].str.strip().map(lambda s: STATE_MAP.get(s.lower(), s))
    c["email_missing"] = c["email"].isna()
    c["email_hash"] = c["email"].map(hash_value)
    c["email_masked"] = c["email"].map(mask_email)
    c["birth_year"] = c["mykad"].map(birth_year_from_mykad)
    c["age_group"] = pd.cut(2026 - c["birth_year"], bins=[0, 24, 34, 44, 54, 120],
                            labels=["<25", "25-34", "35-44", "45-54", "55+"]).astype(str)
    c["signup_date"] = pd.to_datetime(c["signup_date"])
    # data minimisation: name, phone and MyKad are not needed for analytics, so they stop here
    c = c[["customer_id", "state", "age_group", "email_hash", "email_masked", "email_missing", "signup_date"]]

    assert_unique(c, "customer_id", "customers")
    assert_not_null(c, "state", "customers")
    return c


def clean_orders(customers, books):
    o = pd.read_csv(f"{BRONZE}/orders.csv").drop_duplicates()
    iso = pd.to_datetime(o["order_date"], format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(o["order_date"], format="%d/%m/%Y", errors="coerce")
    o["order_date"] = iso.fillna(dmy)

    reasons = pd.Series("", index=o.index)
    reasons[o["quantity"] <= 0] += "invalid quantity;"
    reasons[~o["customer_id"].isin(customers["customer_id"])] += "unknown customer;"
    reasons[~o["book_id"].isin(books["book_id"])] += "unknown book;"
    reasons[o["order_date"].isna()] += "bad date;"
    bad = reasons != ""
    o[bad].assign(reason=reasons[bad]).to_csv(f"{SILVER}/quarantine_orders.csv", index=False)
    o = o[~bad].copy()

    assert_unique(o, "order_id", "orders")
    assert_between(o, "quantity", 1, 100, "orders")
    assert_foreign_key(o, "customer_id", customers, "customer_id", "orders")
    assert_foreign_key(o, "book_id", books, "book_id", "orders")
    print(f"orders: {bad.sum()} rows quarantined")
    return o


def clean_reviews(customers, books):
    r = pd.read_csv(f"{BRONZE}/reviews.csv").drop_duplicates()
    r["has_text"] = r["review_text"].notna()
    r["review_text"] = r["review_text"].map(redact_text)
    r["review_date"] = pd.to_datetime(r["review_date"])

    assert_unique(r, "review_id", "reviews")
    assert_between(r, "stars", 1, 5, "reviews")
    assert_foreign_key(r, "customer_id", customers, "customer_id", "reviews")
    leaks = r["review_text"].str.contains(PHONE_RE, na=False).sum()
    expect(leaks == 0, f"reviews.review_text: {leaks} phone numbers left after redaction")
    return r


def run():
    os.makedirs(SILVER, exist_ok=True)
    books = clean_books()
    customers = clean_customers()
    orders = clean_orders(customers, books)
    reviews = clean_reviews(customers, books)
    for name, df in [("books", books), ("customers", customers), ("orders", orders), ("reviews", reviews)]:
        df.to_parquet(f"{SILVER}/{name}.parquet", index=False,
                      coerce_timestamps="us", allow_truncated_timestamps=True)
        print(f"silver/{name}.parquet: {len(df)} rows")


if __name__ == "__main__":
    run()
