from __future__ import annotations

"""Official university/lab news discovery.

Many organisations have retired public RSS feeds.  Each source therefore has an RSS
URL where one remains available plus its official news page as a fallback.  The
fallback is deliberately visible in the run log; it is not silently treated as RSS.
"""

import hashlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import feedparser
import requests

HEADERS = {"User-Agent": "ResearchOS/1.0 (personal research discovery tool)"}
TIMEOUT = 20

# Add a source here. Keep the page URL even if it currently has an RSS URL: it is
# the resilience path when a publisher changes or retires its feed.
NEWS_SOURCES = {
    "Oxford": {
        "rss": "https://www.cs.ox.ac.uk/feeds/News-All.xml",
        "page": "https://www.cs.ox.ac.uk/news-events/latest-news.html",
    },
    "Cambridge": {"rss": None, "page": "https://www.cam.ac.uk/news"},
    "DeepMind": {"rss": None, "page": "https://deepmind.google/discover/blog/"},
    "Anthropic": {"rss": None, "page": "https://www.anthropic.com/news"},
    "OpenAI": {"rss": None, "page": "https://openai.com/news/"},
}


class _LinkCollector(HTMLParser):
    """Small dependency-free extractor for article-looking links from news pages."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                self._href, self._text = href, []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            title = " ".join("".join(self._text).split())
            self.links.append((title, self._href))
            self._href, self._text = "", []


def _normal(label: str, title: str, url: str, summary: str = "", published: str = "") -> dict:
    return {
        "id": "rss:" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
        "title": title,
        "authors": [label],
        "abstract": summary,
        "source": "rss",
        "url": url,
        "doi": "",
        "published_date": (published or "")[:10],
        "topics": [],
        "universities": [],
        "researchers": [],
    }


def _fetch(url: str) -> bytes:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def _from_rss(label: str, url: str) -> list[dict]:
    feed = feedparser.parse(_fetch(url))
    if feed.bozo and not feed.entries:
        raise ValueError(str(feed.bozo_exception))
    return [
        _normal(label, entry.get("title", "Untitled"), entry.get("link", ""), entry.get("summary", ""), entry.get("published", entry.get("updated", "")))
        for entry in feed.entries[:20]
        if entry.get("link")
    ]


def _from_news_page(label: str, page_url: str) -> list[dict]:
    parser = _LinkCollector()
    parser.feed(_fetch(page_url).decode("utf-8", errors="replace"))
    ignored = {"home", "news", "research", "about", "careers", "support", "privacy", "terms", "contact", "learn more", "read more", "sign in", "log in"}
    page_host = urlparse(page_url).netloc
    items, seen = [], set()
    for title, href in parser.links:
        url = urljoin(page_url, href)
        if not title or title.casefold() in ignored or len(title) < 18 or url in seen:
            continue
        if urlparse(url).netloc != page_host or urlparse(url).path in ("", "/"):
            continue
        seen.add(url)
        items.append(_normal(label, title, url))
        if len(items) == 20:
            break
    return items


def discover_news(config: dict) -> list[dict]:
    if not config["sources"].get("university_rss"):
        return []
    configured_universities = {entry["name"] for entry in config["universities"]}
    items: list[dict] = []
    for label, source in NEWS_SOURCES.items():
        found: list[dict] = []
        rss_url = source.get("rss")
        if rss_url:
            try:
                found = _from_rss(label, rss_url)
                print(f"RSS {label}: retrieved {len(found)} items.")
            except (requests.RequestException, ValueError) as exc:
                print(f"RSS {label}: unavailable ({exc}); using official news-page fallback.")
        if not found:
            try:
                found = _from_news_page(label, source["page"])
                print(f"News page {label}: retrieved {len(found)} items.")
            except requests.RequestException as exc:
                print(f"News page {label}: unavailable ({exc}).")
        for item in found:
            if label in configured_universities:
                item["universities"] = [label]
        items.extend(found)
    return list({item["id"]: item for item in items}.values())
