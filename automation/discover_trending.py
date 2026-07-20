from __future__ import annotations

"""Current AI stories grouped into transparent, source-backed trending topics."""

import hashlib
import re
from urllib.parse import urlencode

import feedparser
import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "ResearchOS/1.0 (personal research discovery tool)"}
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?"
SEARCHES = (
    '"artificial intelligence" when:7d',
    '"machine learning" when:7d',
    '"AI agents" when:7d',
    '"AI safety" OR "AI policy" when:7d',
)
TOPIC_RULES = (
    ("AI safety, governance and policy", {"safety", "policy", "policies", "regulation", "regulatory", "governance", "ethics", "risk", "law", "legal", "legislation", "copyright"}),
    ("AI agents, robotics and autonomy", {"agent", "agents", "robot", "robots", "robotics", "autonomous", "autonomy", "physical"}),
    ("AI models, products and capabilities", {"model", "models", "llm", "gpt", "claude", "gemini", "release", "released", "launch", "product", "chatbot"}),
    ("AI in science and health", {"science", "scientific", "drug", "drugs", "health", "healthcare", "medical", "medicine", "biology", "protein", "researchers"}),
    ("AI infrastructure, chips and energy", {"chip", "chips", "gpu", "gpus", "nvidia", "compute", "computing", "datacenter", "data", "center", "energy"}),
    ("AI business, work and education", {"business", "company", "companies", "funding", "jobs", "work", "workplace", "school", "schools", "teacher", "teachers", "education", "startup"}),
    ("AI media, creativity and culture", {"image", "images", "video", "videos", "music", "creative", "film", "media", "artist", "artists"}),
)


def _topic_for(headline: str) -> str:
    words = set(re.findall(r"[a-z0-9]{3,}", headline.casefold()))
    best_topic, best_matches = "AI research and adoption", 0
    for topic, keywords in TOPIC_RULES:
        matches = len(words & keywords)
        if matches > best_matches:
            best_topic, best_matches = topic, matches
    return best_topic


def _headline(entry) -> str:
    title = " ".join(entry.get("title", "").split())
    source_title = entry.get("source", {}).get("title", "")
    suffix = f" - {source_title}"
    return title[:-len(suffix)].strip() if source_title and title.endswith(suffix) else title


def _fetch_articles() -> list[dict]:
    articles, seen = [], set()
    for query in SEARCHES:
        url = GOOGLE_NEWS_RSS + urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except requests.RequestException as exc:
            print(f"Trending search unavailable ({query}): {exc}")
            continue
        for entry in feed.entries[:20]:
            headline, link = _headline(entry), entry.get("link", "")
            if not headline or not link or headline.casefold() in seen:
                continue
            seen.add(headline.casefold())
            articles.append({
                "id": "google_news:" + hashlib.sha256((headline + link).encode("utf-8")).hexdigest()[:24],
                "title": headline,
                "authors": [entry.get("source", {}).get("title", "Unknown source")],
                "abstract": entry.get("summary", ""),
                "source": "google_news",
                "url": link,
                "doi": "",
                "published_date": entry.get("published", "")[:10],
                "topics": [], "universities": [], "researchers": [], "relevance_score": 0,
            })
    return articles


def _cluster_articles(articles: list[dict]) -> list[dict]:
    """Group articles into transparent AI topics; score = reports + 2 per outlet."""
    groups: dict[str, list[dict]] = {}
    for article in articles:
        groups.setdefault(_topic_for(article["title"]), []).append(article)
    for topic, topic_articles in groups.items():
        outlets = {article["authors"][0] for article in topic_articles}
        score = len(topic_articles) + (2 * len(outlets))
        for article in topic_articles:
            article["trend_topic"] = topic
            article["trend_score"] = float(score)
    return sorted(articles, key=lambda article: (-float(article["trend_score"]), article["trend_topic"], article["title"]))


def discover_trending(config: dict) -> list[dict]:
    if not config["sources"].get("duckduckgo_trending"):
        return []
    # The config key is retained for backwards compatibility. The old broad
    # DuckDuckGo web search returned category pages, so v1 now uses current
    # news headlines and reports the provider honestly in each stored item.
    articles = _cluster_articles(_fetch_articles())
    grouped = len({article["trend_topic"] for article in articles})
    print(f"Trending news: {len(articles)} articles across {grouped} topic groups.")
    return articles
