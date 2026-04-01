"""
explore_data.py
Prints a summary of the fetched Wikipedia + GDELT CSVs.
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

WIKI_CSV  = os.path.join(DATA_DIR, "wikipedia_pageviews.csv")
GDELT_CSV = os.path.join(DATA_DIR, "gdelt_coverage.csv")


def summarise_wikipedia():
    if not os.path.exists(WIKI_CSV):
        print("  [!] wikipedia_pageviews.csv not found — run fetch_attention_data.py first")
        return

    df = pd.read_csv(WIKI_CSV, parse_dates=["date"])
    print(f"\n{'─'*55}")
    print("  WIKIPEDIA PAGEVIEWS")
    print(f"{'─'*55}")
    print(f"  Total rows   : {len(df):,}")
    print(f"  Date range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Articles     : {df['article'].nunique()}")
    print()

    # Per-article totals
    agg = (
        df.groupby("article")
        .agg(total_views=("views", "sum"), days=("date", "nunique"))
        .sort_values("total_views", ascending=False)
    )
    agg["zero_days"] = df.groupby("article").apply(lambda x: (x["views"] == 0).sum()).values

    print(f"  {'Article':<40} {'Total Views':>14} {'Days':>6} {'Zero Days':>10}")
    print(f"  {'─'*40} {'─'*14} {'─'*6} {'─'*10}")
    for article, row in agg.iterrows():
        flag = " ⚠" if row["zero_days"] > 0 else ""
        print(
            f"  {article:<40} {row['total_views']:>14,.0f} "
            f"{row['days']:>6} {row['zero_days']:>10}{flag}"
        )

    zero_articles = agg[agg["total_views"] == 0].index.tolist()
    if zero_articles:
        print(f"\n  [!] Articles with ALL-ZERO views: {zero_articles}")
    else:
        print("\n  No articles with all-zero data.")


def summarise_gdelt():
    if not os.path.exists(GDELT_CSV):
        print("  [!] gdelt_coverage.csv not found — run fetch_attention_data.py first")
        return

    df = pd.read_csv(GDELT_CSV, parse_dates=["date"])
    print(f"\n{'─'*55}")
    print("  GDELT NEWS COVERAGE")
    print(f"{'─'*55}")
    print(f"  Total rows   : {len(df):,}")
    print(f"  Date range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Terms        : {df['term'].nunique()}")
    print()

    agg = (
        df.groupby("term")
        .agg(total_volume=("volume", "sum"), days=("date", "nunique"))
        .sort_values("total_volume", ascending=False)
    )
    agg["zero_days"] = df.groupby("term").apply(lambda x: (x["volume"] == 0).sum()).values

    print(f"  {'Term':<35} {'Total Volume':>14} {'Days':>6} {'Zero Days':>10}")
    print(f"  {'─'*35} {'─'*14} {'─'*6} {'─'*10}")
    for term, row in agg.iterrows():
        flag = " ⚠" if row["zero_days"] > 0 else ""
        print(
            f"  {term:<35} {row['total_volume']:>14.2f} "
            f"{row['days']:>6} {row['zero_days']:>10}{flag}"
        )

    zero_terms = agg[agg["total_volume"] == 0].index.tolist()
    if zero_terms:
        print(f"\n  [!] Terms with ALL-ZERO volume: {zero_terms}")
    else:
        print("\n  No terms with all-zero data.")


if __name__ == "__main__":
    print("\n========================================")
    print("  GAZE ECONOMY — DATA SUMMARY")
    print("========================================")
    summarise_wikipedia()
    summarise_gdelt()
    print(f"\n{'─'*55}\n")
