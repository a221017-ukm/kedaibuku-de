"""Lab 3: scrape the book catalogue from books.toscrape.com (a practice site built for scraping).

Run from the project folder:  python src/extract_books.py
"""
import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/"
HEADERS = {"User-Agent": "TTTC3213-student-lab (educational use)"}


def get_soup(url):
    """Download one web page and turn its HTML into a searchable object."""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()               # stop with an error if the page failed to load
    response.encoding = "utf-8"               # keeps the £ sign readable
    return BeautifulSoup(response.text, "lxml")


def list_categories():
    """Return (name, link) for every category in the site's left-hand menu."""
    soup = get_soup(urljoin(BASE, "index.html"))
    links = soup.select("div.side_categories ul li ul li a")
    return [(a.get_text(strip=True), urljoin(BASE, a["href"])) for a in links]


def scrape_category(name, url):
    """Collect every book in one category, following the 'next' button page by page."""
    rows = []
    while url:
        soup = get_soup(url)
        for pod in soup.select("article.product_pod"):          # one box per book
            link = pod.select_one("h3 a")
            detail_url = urljoin(url, link["href"])
            rows.append({
                "book_id": detail_url.rstrip("/").split("/")[-2],
                "title": link["title"],
                "category": name,
                "price_raw": pod.select_one("p.price_color").get_text(strip=True),
                "rating_raw": pod.select_one("p.star-rating")["class"][1],
                "availability": pod.select_one("p.availability").get_text(strip=True),
                "url": detail_url,
            })
        next_link = soup.select_one("li.next a")
        url = urljoin(url, next_link["href"]) if next_link else None
        time.sleep(0.5)                       # be polite: one request per half second
    return rows


def run():
    os.makedirs("data/lake/bronze", exist_ok=True)
    all_rows = []
    for name, url in list_categories():
        print("Scraping", name)
        all_rows += scrape_category(name, url)
    df = pd.DataFrame(all_rows)
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()   # when we collected it
    df.to_csv("data/lake/bronze/books.csv", index=False)
    print(f"Saved {len(df)} books")


if __name__ == "__main__":
    run()
