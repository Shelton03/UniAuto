from __future__ import annotations
import hashlib
import os
import re
import time
from datetime import date
from urllib.parse import quote
import feedparser
import requests
from automation.config import names
from dotenv import load_dotenv
from automation.config import ROOT

TIMEOUT = 20
HEADERS = {"User-Agent": "ResearchOS/1.0 (personal research tool)"}
load_dotenv(ROOT / ".env")

def _semantic_headers() -> dict[str, str]:
    headers = dict(HEADERS)
    if key := os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = key
    return headers

def _id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode()).hexdigest()[:24]}"

def _normal(title, source, *, authors=None, abstract="", url="", doi="", published_date="", source_id=""):
    return {"id": doi.lower() if doi else _id(source, source_id or url or title), "title": title.strip(), "authors": authors or [], "abstract": abstract or "", "source": source, "url": url, "doi": doi or "", "published_date": (published_date or "")[:10], "topics": [], "universities": [], "researchers": []}

def _queries(config):
    # Universities are enrichment tags only. Searching them would flood the
    # digest with unrelated work from large institutions.
    areas = [f"AI {area}" if area.casefold() == "reasoning" else area for area in names(config, "research_areas")]
    return names(config, "research_questions") + areas + names(config, "researchers")

def _title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()

def _source_weight(item: dict) -> tuple[int, int, int]:
    """Prefer a record with an abstract, DOI, and a paper-focused source."""
    priority = {"semantic_scholar": 3, "arxiv": 2, "openalex": 1}
    return (bool(item.get("abstract")), bool(item.get("doi")), priority.get(item.get("source"), 0))

def _merge_paper_records(items: list[dict]) -> list[dict]:
    """One review card per publication even when APIs use different IDs."""
    merged: dict[str, dict] = {}
    for item in items:
        # DOI quality differs by provider; title is the common cross-source
        # identity for the review digest, with DOI retained on the chosen item.
        key = f"title:{_title_key(item['title'])}"
        existing = merged.get(key)
        if not existing:
            merged[key] = item
            continue
        preferred, alternate = (item, existing) if _source_weight(item) > _source_weight(existing) else (existing, item)
        preferred["authors"] = list(dict.fromkeys(preferred.get("authors", []) + alternate.get("authors", [])))
        preferred["universities"] = list(dict.fromkeys(preferred.get("universities", []) + alternate.get("universities", [])))
        if not preferred.get("abstract"):
            preferred["abstract"] = alternate.get("abstract", "")
        if not preferred.get("doi"):
            preferred["doi"] = alternate.get("doi", "")
        merged[key] = preferred
    return list(merged.values())

def discover_arxiv(config: dict) -> list[dict]:
    items = []
    for term in _queries(config)[:8]:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote(term)}&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except requests.RequestException as exc: print(f"arXiv {term}: {exc}"); continue
        for entry in feed.entries:
            items.append(_normal(entry.title, "arxiv", authors=[a.name for a in entry.get("authors", [])], abstract=entry.get("summary", ""), url=entry.get("link", ""), published_date=entry.get("published", ""), source_id=entry.get("id", "")))
    return items

def discover_openalex(config: dict) -> list[dict]:
    items = []
    for term in _queries(config)[:8]:
        try:
            response = requests.get("https://api.openalex.org/works", params={"search": term, "per-page": 10, "sort": "publication_date:desc"}, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc: print(f"OpenAlex {term}: {exc}"); continue
        if "results" not in data:
            print(f"OpenAlex {term}: unexpected API response: {data.get('error', data.get('message', 'no results field'))}")
            continue
        for work in data.get("results", []):
            authors = [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])]
            institutions = [i.get("display_name", "") for a in work.get("authorships", []) for i in a.get("institutions", [])]
            doi = (work.get("doi") or "").removeprefix("https://doi.org/")
            items.append(_normal(work.get("title", "Untitled"), "openalex", authors=authors, abstract="", url=work.get("doi") or work.get("id", ""), doi=doi, published_date=work.get("publication_date", ""), source_id=work.get("id", "")) | {"universities": institutions})
    return items

def discover_semantic_scholar(config: dict) -> list[dict]:
    items = []
    fields = "title,abstract,authors,externalIds,url,publicationDate,paperId"
    queries = _queries(config)[:8]
    for index, term in enumerate(queries):
        try:
            response = requests.get("https://api.semanticscholar.org/graph/v1/paper/search", params={"query": term, "limit": 10, "fields": fields}, headers=_semantic_headers(), timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"Semantic Scholar {term}: {exc}")
        else:
            if "data" not in data:
                print(f"Semantic Scholar {term}: unexpected API response: {data.get('error', data.get('message', 'no data field'))}")
            else:
                for paper in data.get("data", []):
                    doi = paper.get("externalIds", {}).get("DOI", "")
                    items.append(_normal(paper.get("title", "Untitled"), "semantic_scholar", authors=[a.get("name", "") for a in paper.get("authors", [])], abstract=paper.get("abstract", ""), url=paper.get("url", ""), doi=doi, published_date=paper.get("publicationDate", ""), source_id=paper.get("paperId", "")))
        if index < len(queries) - 1:
            time.sleep(1.1)  # Semantic Scholar's anonymous endpoint is rate-limited.
    return items

def discover_papers(config: dict) -> list[dict]:
    result = []
    if config["sources"].get("arxiv"):
        arxiv = discover_arxiv(config); result += arxiv; print(f"arXiv: {len(arxiv)} candidates.")
    if config["sources"].get("openalex"):
        openalex = discover_openalex(config); result += openalex; print(f"OpenAlex: {len(openalex)} candidates.")
    if config["sources"].get("semantic_scholar"):
        if not os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
            print("Semantic Scholar: no API key configured; shared anonymous requests may be throttled.")
        semantic = discover_semantic_scholar(config); result += semantic; print(f"Semantic Scholar: {len(semantic)} candidates.")
    return _merge_paper_records(result)
