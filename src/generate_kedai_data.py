"""Generate synthetic KedaiBuku.my customers, orders and reviews (bronze layer).

Usage (from the project root):
    python src/generate_kedai_data.py --seed 123456

Use the digits of your matric number as the seed, so your dataset is unique.
The data is fake, but treat it as real personal data (PDPA practice).
"""
import argparse
import random
from datetime import date, timedelta

import pandas as pd

MALAY_FIRST = ["Ahmad", "Nur", "Siti", "Muhammad", "Aisyah", "Hafiz", "Farah", "Amir", "Nurul", "Iskandar"]
MALAY_LAST = ["Abdullah", "Ismail", "Rahman", "Hassan", "Yusof", "Omar", "Ibrahim", "Salleh"]
CHINESE = ["Tan Wei Ming", "Lim Mei Ling", "Wong Kah Wai", "Lee Jia Hui", "Ng Chee Keong", "Chong Siew Lan"]
INDIAN = ["Arjun a/l Rajan", "Kavitha a/p Suresh", "Ravi a/l Muthu", "Priya a/p Ganesan", "Vinod a/l Kumar"]

STATES = {  # state name -> MyKad place-of-birth code
    "Johor": "01", "Kedah": "02", "Kelantan": "03", "Melaka": "04", "Negeri Sembilan": "05",
    "Pahang": "06", "Pulau Pinang": "07", "Perak": "08", "Selangor": "10", "Terengganu": "11",
    "Sabah": "12", "Sarawak": "13", "WP Kuala Lumpur": "14",
}
STATE_MESS = {"Selangor": ["selangor", " SELANGOR ", "SGR"], "WP Kuala Lumpur": ["Kuala Lumpur", "KL"],
              "Pulau Pinang": ["Penang", "P. Pinang"], "Johor": ["johor", "JHR"]}

# Review sentences by aspect, polarity and language (about 1 in 4 reviews is in Malay)
REVIEW_TEXT = {
    "en": {
        "delivery":  {"pos": ["Delivery was fast, it arrived in two days.", "The parcel came earlier than expected."],
                      "neg": ["Delivery took almost three weeks.", "The parcel was lost and arrived very late."]},
        "packaging": {"pos": ["Well packed, the book was in perfect condition.", "Nicely wrapped with bubble wrap."],
                      "neg": ["The cover was torn when it arrived.", "Pages were bent and the box was crushed."]},
        "price":     {"pos": ["Great value for the price.", "Cheaper than the bookshops in town."],
                      "neg": ["Too expensive for such a thin book.", "Overpriced compared to other shops."]},
        "content":   {"pos": ["The story kept me hooked until the last page.", "Very well written and easy to follow."],
                      "neg": ["The plot was boring and predictable.", "Too many typos and the writing is weak."]},
        "service":   {"pos": ["The seller replied quickly and was very helpful.", "Customer support sorted out my issue in a day."],
                      "neg": ["Customer service never answered my emails.", "No response when I asked for a refund."]},
    },
    "ms": {
        "delivery":  {"pos": ["Penghantaran sangat cepat, sampai dalam dua hari."],
                      "neg": ["Barang sampai lambat, hampir tiga minggu.", "Parcel hilang dan lambat sampai."]},
        "packaging": {"pos": ["Bungkusan kemas, buku dalam keadaan baik."],
                      "neg": ["Kulit buku koyak semasa sampai.", "Kotak remuk dan halaman buku berlipat."]},
        "price":     {"pos": ["Harga berpatutan dan sangat berbaloi."],
                      "neg": ["Terlalu mahal untuk buku yang nipis."]},
        "content":   {"pos": ["Jalan cerita sangat menarik, tak boleh berhenti baca."],
                      "neg": ["Cerita membosankan dan mudah diteka."]},
        "service":   {"pos": ["Penjual cepat membalas dan sangat membantu."],
                      "neg": ["Khidmat pelanggan langsung tidak membalas mesej saya."]},
    },
}


def make_review_text(rng, stars):
    lang = "ms" if rng.random() < 0.25 else "en"
    aspects = rng.sample(list(REVIEW_TEXT[lang]), k=rng.choice([1, 1, 2]))
    polarity = "pos" if stars >= 4 else "neg" if stars <= 2 else rng.choice(["pos", "neg"])
    if rng.random() < 0.1:                                     # 10% text disagrees with the stars
        polarity = "neg" if polarity == "pos" else "pos"
    return " ".join(rng.choice(REVIEW_TEXT[lang][a][polarity]) for a in aspects)


def make_name(rng):
    group = rng.random()
    if group < 0.6:
        first = rng.choice(MALAY_FIRST)
        joiner = " binti " if first in {"Nur", "Siti", "Aisyah", "Farah", "Nurul"} else " bin "
        return first + joiner + rng.choice(MALAY_LAST)
    return rng.choice(CHINESE if group < 0.85 else INDIAN)


def make_mykad(rng, state):
    dob = date(1960, 1, 1) + timedelta(days=rng.randint(0, 16000))
    return f"{dob:%y%m%d}-{STATES[state]}-{rng.randint(0, 9999):04d}"


def make_phone(rng):
    number = f"01{rng.choice('0123456789')}{rng.randint(1000000, 9999999)}"
    style = rng.random()
    if style < 0.6:
        return f"{number[:3]}-{number[3:]}"
    if style < 0.8:
        return "+6" + number
    return number


def customers(rng, n=500):
    rows = []
    for i in range(1, n + 1):
        name = make_name(rng)
        state = rng.choice(list(STATES))
        handle = name.lower().replace(" a/l ", ".").replace(" a/p ", ".").replace(" bin ", ".").replace(" binti ", ".").replace(" ", ".")
        rows.append({
            "customer_id": f"C{i:04d}",
            "full_name": name,
            "email": f"{handle}{rng.randint(1, 99)}@{rng.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}",
            "phone": make_phone(rng),
            "mykad": make_mykad(rng, state),
            "state": rng.choice(STATE_MESS[state]) if state in STATE_MESS and rng.random() < 0.3 else state,
            "signup_date": str(date(2024, 1, 1) + timedelta(days=rng.randint(0, 800))),
        })
    df = pd.DataFrame(rows)
    df.loc[df.sample(frac=0.05, random_state=rng.randint(0, 10**6)).index, "email"] = None   # missing emails
    dupes = df.sample(frac=0.03, random_state=rng.randint(0, 10**6))                          # duplicate rows
    return pd.concat([df, dupes]).sample(frac=1, random_state=rng.randint(0, 10**6)).reset_index(drop=True)


def orders(rng, customer_ids, book_ids, n=3000):
    rows = []
    for i in range(1, n + 1):
        d = date(2026, 1, 1) + timedelta(days=rng.randint(0, 240))
        rows.append({
            "order_id": f"O{i:05d}",
            "customer_id": rng.choice(customer_ids) if rng.random() > 0.01 else f"C{rng.randint(9000, 9999)}",  # 1% orphans
            "book_id": rng.choice(book_ids),
            "quantity": rng.choice([1, 1, 1, 2, 2, 3]) if rng.random() > 0.01 else rng.choice([0, -1]),      # 1% invalid
            "order_date": d.strftime("%d/%m/%Y") if rng.random() < 0.03 else str(d),                           # 3% odd format
        })
    df = pd.DataFrame(rows)
    return pd.concat([df, df.sample(frac=0.02, random_state=rng.randint(0, 10**6))]).reset_index(drop=True)


def reviews(rng, customer_ids, book_ids, n=1200):
    rows = []
    for i in range(1, n + 1):
        stars = rng.choice([1, 2, 3, 4, 4, 5, 5, 5])
        text = make_review_text(rng, stars)
        if rng.random() < 0.02:                                 # 2% leak personal data in free text
            text += f" Contact me at {make_phone(rng)} for a swap."
        if rng.random() < 0.03:
            text = None
        rows.append({
            "review_id": f"R{i:05d}",
            "customer_id": rng.choice(customer_ids),
            "book_id": rng.choice(book_ids),
            "stars": stars,
            "review_text": text,
            "review_date": str(date(2026, 1, 1) + timedelta(days=rng.randint(0, 240))),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, help="digits of your matric number")
    parser.add_argument("--books", default="data/lake/bronze/books.csv")
    parser.add_argument("--out", default="data/lake/bronze")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    book_ids = pd.read_csv(args.books)["book_id"].tolist()
    cust = customers(rng)
    cust_ids = cust["customer_id"].unique().tolist()

    cust.to_csv(f"{args.out}/customers.csv", index=False)
    orders(rng, cust_ids, book_ids).to_csv(f"{args.out}/orders.csv", index=False)
    reviews(rng, cust_ids, book_ids).to_csv(f"{args.out}/reviews.csv", index=False)
    print("Wrote customers.csv, orders.csv and reviews.csv to", args.out)
