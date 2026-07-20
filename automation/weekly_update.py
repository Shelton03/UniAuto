from __future__ import annotations

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from automation.config import load_config
from automation.discover_papers import discover_papers
from automation.discover_news import discover_news
from automation.discover_trending import discover_trending
from automation.rank_papers import rank_items
from automation import state_store

def run() -> dict[str, int]:
    config = load_config()
    print("Research OS weekly update started.", flush=True)
    print("Discovering personalised papers...", flush=True)
    papers = rank_items(discover_papers(config), config)
    print(f"Found {len(papers)} paper candidates.", flush=True)
    print("Discovering university and lab news...", flush=True)
    news = rank_items(discover_news(config), config)
    regular = papers + news
    print(f"Found {len(news)} news items.", flush=True)
    print("Discovering general AI trending items...", flush=True)
    trending = discover_trending(config)
    print(f"Found {len(trending)} current trending-news articles.", flush=True)
    for item in regular + trending: state_store.upsert_item(item)
    digest_id = state_store.create_digest([i["id"] for i in regular], [i["id"] for i in trending])
    print(f"Saved digest #{digest_id}: {len(regular)} ranked items, {len(trending)} trending items.", flush=True)
    return {"ranked": len(regular), "trending": len(trending)}

if __name__ == "__main__":
    try: run()
    except Exception as exc:
        print(f"Update failed: {exc}", file=sys.stderr, flush=True)
        raise
