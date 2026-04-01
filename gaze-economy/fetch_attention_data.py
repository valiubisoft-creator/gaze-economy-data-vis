"""
fetch_attention_data.py
Pulls Wikipedia pageview data + GDELT news coverage for Oct 2023 → Mar 2026.
Saves CSVs to ./data/
"""

import requests
import pandas as pd
import time
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

HEADERS = {
    "User-Agent": "GazeEconomyResearch/1.0 (gazeeconomy@research.com)"
}

# Wikipedia article names (underscores for spaces)
WIKI_ARTICLES = [
    "Attention_economy",
    "TikTok",
    "Instagram",
    "YouTube",
    "Twitter",
    "Artificial_intelligence",
    "ChatGPT",
    "Gaza_Strip",
    "Taylor_Swift",
    "OpenAI",
    "Elon_Musk",
    "Climate_change",
    "Generative_artificial_intelligence",
    "Misinformation",
    "Deepfake",
]

# GDELT search terms (plain text)
GDELT_TERMS = [
    "attention economy",
    "TikTok",
    "Instagram",
    "YouTube",
    "Twitter",
    "artificial intelligence",
    "ChatGPT",
    "Gaza",
    "Taylor Swift",
    "OpenAI",
    "Elon Musk",
    "climate change",
    "generative AI",
    "misinformation",
    "deepfake",
]

WIKI_START = "2023100100"
WIKI_END   = "2026033100"
GDELT_START = "20231001000000"
GDELT_END   = "20260331000000"


def fetch_with_retry(url, max_retries=3, delay=2):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            if resp.status_code == 200:
                return resp
            print(f"    [attempt {attempt}] HTTP {resp.status_code} — skipping")
        except Exception as exc:
            print(f"    [attempt {attempt}] Error: {exc}")
        if attempt < max_retries:
            time.sleep(delay)
    return None


# ─── Wikipedia ───────────────────────────────────────────────────────────────

def fetch_wikipedia_pageviews():
    print("\n=== Wikipedia Pageviews ===")
    rows = []

    for article in WIKI_ARTICLES:
        encoded = urllib.parse.quote(article, safe="")
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
            f"/en.wikipedia/all-access/all-agents/{encoded}/daily"
            f"/{WIKI_START}/{WIKI_END}"
        )
        print(f"  {article} ...", end=" ", flush=True)
        resp = fetch_with_retry(url)

        if resp is None:
            print("SKIP")
            continue

        items = resp.json().get("items", [])
        for item in items:
            rows.append({
                "article": article,
                "date": item["timestamp"][:8],   # YYYYMMDD
                "views": item["views"],
            })
        print(f"{len(items)} days")
        time.sleep(0.4)

    if not rows:
        print("No Wikipedia data fetched.")
        return

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    out = os.path.join(DATA_DIR, "wikipedia_pageviews.csv")
    df.to_csv(out, index=False)
    print(f"\n  Saved {len(df):,} rows → {out}")


# ─── GDELT ───────────────────────────────────────────────────────────────────

def fetch_gdelt_coverage():
    print("\n=== GDELT News Coverage ===")
    rows = []

    for term in GDELT_TERMS:
        encoded = urllib.parse.quote(term)
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={encoded}"
            f"&mode=timelinevol"
            f"&format=json"
            f"&startdatetime={GDELT_START}"
            f"&enddatetime={GDELT_END}"
            f"&TIMELINERES=day"
        )
        print(f"  {term!r} ...", end=" ", flush=True)
        resp = fetch_with_retry(url)

        if resp is None:
            print("SKIP")
            continue

        try:
            payload = resp.json()
            # GDELT returns: {"timeline": [{"series": "Volume Intensity", "data": [...]}]}
            timeline = payload.get("timeline", [])
            data_points = []
            if timeline:
                data_points = timeline[0].get("data", [])

            for pt in data_points:
                raw_date = str(pt.get("date", ""))[:8]   # YYYYMMDD
                if len(raw_date) == 8:
                    rows.append({
                        "term": term,
                        "date": raw_date,
                        "volume": pt.get("value", 0.0),
                    })
            print(f"{len(data_points)} points")
        except Exception as exc:
            print(f"parse error: {exc}")

        time.sleep(0.8)

    if not rows:
        print("No GDELT data fetched.")
        return

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    out = os.path.join(DATA_DIR, "gdelt_coverage.csv")
    df.to_csv(out, index=False)
    print(f"\n  Saved {len(df):,} rows → {out}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    os.makedirs(DATA_DIR, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "wiki"):
        fetch_wikipedia_pageviews()
    if mode in ("all", "gdelt"):
        fetch_gdelt_coverage()
    print("\nAll done.")
