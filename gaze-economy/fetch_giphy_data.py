"""
fetch_giphy_data.py
===================
Gaze Economy — Visual Codification Layer
Extracts GIF count + top GIF per keyword from GIPHY API.

What this measures:
  total_count = how many GIFs exist for a term
              = proxy for visual codification in popular culture
              = how thoroughly a concept has been absorbed into
                meme/image language by the (largely western) internet

⚠ KNOWN LIMITATION — GIPHY FREE TIER API CAP:
  The free tier caps pagination.total_count at 500 regardless of the
  actual number of GIFs indexed for a term. Popular terms like "war"
  or "robot" likely have millions of GIFs but will return 500 here.
  Only under-represented terms (e.g. Deepfake: 145, Ceasefire: 180)
  fall below the cap and reflect genuine scarcity.

  To get real uncapped counts, a GIPHY Production API key is required
  (apply at developers.giphy.com — requires app review and approval).
  Until then, the bubble chart size differentiation is limited to the
  bottom of the range; most bubbles will render at or near max size.

Usage:
  pip install requests
  python fetch_giphy_data.py

Output:
  data/giphy_counts.csv      ← keyword, total_count, top gif url
  data/giphy_raw.json        ← full API responses per keyword
"""

import requests
import json
import csv
import time
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────

API_KEY    = "cOaguO9vKL1gkViYLUGhaPLsSFRxNzXH"   # GIPHY API key
OUTPUT_DIR = "data"
BASE_URL   = "https://api.giphy.com/v1/gifs/search"

# ── KEYWORDS ──────────────────────────────────────────────────────────────────
# Organised into thematic clusters so you can compare within and across groups.
# Each entry: (search_term, label, cluster)

KEYWORDS = [
    # Conflict & crisis
    ("gaza",              "Gaza",           "conflict"),
    ("war",               "War",            "conflict"),
    ("protest",           "Protest",        "conflict"),
    ("ceasefire",         "Ceasefire",      "conflict"),
    ("refugee",           "Refugee",        "conflict"),

    # Platform & attention
    ("tiktok",            "TikTok",         "platform"),
    ("instagram",         "Instagram",      "platform"),
    ("youtube",           "YouTube",        "platform"),
    ("twitter",           "Twitter",        "platform"),
    ("social media",      "Social Media",   "platform"),
    ("going viral",       "Going Viral",    "platform"),
    ("scroll",            "Scrolling",      "platform"),

    # Information & truth
    ("fake news",         "Fake News",      "information"),
    ("misinformation",    "Misinformation", "information"),
    ("deepfake",          "Deepfake",       "information"),
    ("propaganda",        "Propaganda",     "information"),
    ("fact check",        "Fact Check",     "information"),

    # Technology
    ("artificial intelligence", "AI",       "technology"),
    ("chatgpt",           "ChatGPT",        "technology"),
    ("robot",             "Robot",          "technology"),
    ("surveillance",      "Surveillance",   "technology"),

    # Politics & power
    ("donald trump",      "Trump",          "politics"),
    ("election",          "Election",       "politics"),
    ("democracy",         "Democracy",      "politics"),
    ("censorship",        "Censorship",     "politics"),

    # Culture & attention
    ("taylor swift",      "Taylor Swift",   "culture"),
    ("celebrity",         "Celebrity",      "culture"),
    ("influencer",        "Influencer",     "culture"),
    ("attention",         "Attention",      "culture"),
    ("boredom",           "Boredom",        "culture"),

    # Climate
    ("climate change",    "Climate Change", "climate"),
    ("flood",             "Flood",          "climate"),
    ("wildfire",          "Wildfire",       "climate"),
]

# ── FETCH ─────────────────────────────────────────────────────────────────────

def fetch_keyword(term, label, cluster):
    """
    Hits GIPHY search for one term.
    Returns dict with count + top gif metadata.
    
    We request limit=5 so we get a few GIF options,
    but total_count in pagination reflects the full library.
    """
    params = {
        "api_key": API_KEY,
        "q":       term,
        "limit":   5,        # small request — we just want count + top GIFs
        "offset":  0,
        "rating":  "pg-13",  # filter out explicit content
        "lang":    "en",
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)

        if resp.status_code == 429:
            print(f"  ⚠ Rate limited on '{label}' — waiting 10s...")
            time.sleep(10)
            resp = requests.get(BASE_URL, params=params, timeout=10)

        if resp.status_code != 200:
            print(f"  ⚠ Error {resp.status_code} for '{label}'")
            return None

        data = resp.json()
        pagination = data.get("pagination", {})
        total_count = pagination.get("total_count", 0)
        gifs        = data.get("data", [])

        # Extract top gif URL (small/downsized version for web use)
        top_gif_url     = ""
        top_gif_preview = ""
        top_gif_title   = ""

        if gifs:
            top = gifs[0]
            top_gif_title   = top.get("title", "")
            images          = top.get("images", {})
            # 'fixed_width' is a good balance: animated, reasonable size
            top_gif_url     = images.get("fixed_width", {}).get("url", "")
            # 'fixed_width_still' = static preview (no animation)
            top_gif_preview = images.get("fixed_width_still", {}).get("url", "")

        result = {
            "term":            term,
            "label":           label,
            "cluster":         cluster,
            "total_count":     total_count,
            "top_gif_url":     top_gif_url,
            "top_gif_preview": top_gif_preview,
            "top_gif_title":   top_gif_title,
            # store top 5 gif URLs for later use in viz
            "gif_urls":        [
                g.get("images", {}).get("fixed_width", {}).get("url", "")
                for g in gifs
            ],
        }

        print(f"  ✓ {label:<22} total_count: {total_count:>7,}   cluster: {cluster}")
        return result

    except Exception as e:
        print(f"  ⚠ Exception for '{label}': {e}")
        return None


def fetch_all():
    if API_KEY == "YOUR_GIPHY_API_KEY_HERE":
        print("⚠ Update API_KEY in the script before running.")
        print("  Get your key at: https://developers.giphy.com/dashboard/")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = []
    raw     = {}

    print(f"\n━━━ GIPHY KEYWORD COUNTS ({'=':─<40}\n")

    for term, label, cluster in KEYWORDS:
        result = fetch_keyword(term, label, cluster)
        if result:
            results.append(result)
            raw[label] = result
        time.sleep(0.25)   # gentle — GIPHY free tier: 42 req/min

    # ── Save raw JSON ─────────────────────────────────────────────────────────
    raw_path = os.path.join(OUTPUT_DIR, "giphy_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
    print(f"\n✓ Raw JSON → {raw_path}")

    # ── Save flat CSV ─────────────────────────────────────────────────────────
    csv_path = os.path.join(OUTPUT_DIR, "giphy_counts.csv")
    fields   = ["label", "term", "cluster", "total_count",
                "top_gif_url", "top_gif_preview", "top_gif_title"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"✓ CSV → {csv_path}")

    # ── Print ranked summary ──────────────────────────────────────────────────
    print(f"\n━━━ RANKED BY VISUAL CODIFICATION ━━━━━━━━━━━━━━━━━━━━\n")
    sorted_results = sorted(results, key=lambda x: x["total_count"], reverse=True)

    for r in sorted_results:
        bar    = "█" * min(40, r["total_count"] // 10000)
        gap    = " " * (40 - len(bar))
        print(f"  {r['label']:<22} {bar}{gap} {r['total_count']:>8,}")

    print(f"\n━━━ CLUSTERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    clusters = {}
    for r in results:
        c = r["cluster"]
        clusters.setdefault(c, []).append(r)

    for cluster, items in clusters.items():
        total = sum(i["total_count"] for i in items)
        print(f"  {cluster:<14} {total:>10,} total GIFs across {len(items)} terms")

    print(f"\n━━━ INTERESTING GAPS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("  Terms with < 1,000 GIFs = visually under-codified:")
    under = [r for r in results if r["total_count"] < 1000]
    for r in sorted(under, key=lambda x: x["total_count"]):
        print(f"  {r['label']:<22} {r['total_count']:>6,}")

    print("\nNext: run visualise_giphy.html to see the bubble chart")


if __name__ == "__main__":
    fetch_all()
