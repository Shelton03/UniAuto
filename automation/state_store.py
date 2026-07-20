from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from automation.config import ROOT, load_config

DB_PATH = ROOT / "state.db"
SCHEMA = '''
CREATE TABLE IF NOT EXISTS items (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, authors TEXT, abstract TEXT, source TEXT NOT NULL,
 url TEXT, doi TEXT, published_date TEXT, discovered_date TEXT NOT NULL, topics TEXT,
 universities TEXT, researchers TEXT, questions TEXT, relevance_score REAL, status TEXT NOT NULL DEFAULT 'seen',
 promoted_date TEXT, zotero_key TEXT, obsidian_path TEXT, trend_topic TEXT, trend_score REAL,
 review_eligible INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS digests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, run_date TEXT NOT NULL, item_ids TEXT NOT NULL, trending_ids TEXT
);'''

def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Existing state databases predate trend-topic metadata. SQLite's additive
    # migration keeps every already-seen item intact.
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    if "trend_topic" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN trend_topic TEXT")
    if "trend_score" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN trend_score REAL")
    if "review_eligible" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN review_eligible INTEGER NOT NULL DEFAULT 1")
    if "questions" not in columns:
        conn.execute("ALTER TABLE items ADD COLUMN questions TEXT")
    return conn

def _dump(value: Any) -> str:
    return json.dumps(value or [])

def _item(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key in ("authors", "topics", "universities", "researchers", "questions"):
        result[key] = json.loads(result[key] or "[]")
    return result

def upsert_item(item: dict[str, Any]) -> None:
    """Insert a discovery; preserve a user's disposition and integration keys on re-discovery."""
    fields = ["id", "title", "authors", "abstract", "source", "url", "doi", "published_date", "discovered_date", "topics", "universities", "researchers", "questions", "relevance_score", "trend_topic", "trend_score", "review_eligible"]
    values = {**item}
    values.setdefault("discovered_date", date.today().isoformat())
    values.setdefault("review_eligible", 1)
    for key in ("authors", "topics", "universities", "researchers", "questions"):
        values[key] = _dump(values.get(key))
    sql = f'''INSERT INTO items ({','.join(fields)}) VALUES ({','.join(':'+f for f in fields)})
      ON CONFLICT(id) DO UPDATE SET
      title=excluded.title, authors=excluded.authors, abstract=excluded.abstract, source=excluded.source,
      url=excluded.url, doi=excluded.doi, published_date=excluded.published_date,
      topics=excluded.topics, universities=excluded.universities, researchers=excluded.researchers, questions=excluded.questions,
      relevance_score=excluded.relevance_score, trend_topic=excluded.trend_topic,
      trend_score=excluded.trend_score, review_eligible=excluded.review_eligible'''
    with connection() as conn:
        conn.execute(sql, {f: values.get(f) for f in fields})

def mark_promoted(item_id: str, zotero_key: str | None = None, obsidian_path: str | None = None) -> None:
    if not zotero_key and not obsidian_path:
        raise ValueError("Provide a Zotero key and/or Obsidian path")
    with connection() as conn:
        conn.execute("""UPDATE items SET status='promoted', promoted_date=COALESCE(promoted_date, ?),
          zotero_key=COALESCE(?, zotero_key), obsidian_path=COALESCE(?, obsidian_path) WHERE id=?""",
          (date.today().isoformat(), zotero_key, obsidian_path, item_id))

def mark_dismissed(item_id: str) -> None:
    with connection() as conn:
        conn.execute("UPDATE items SET status='dismissed' WHERE id=?", (item_id,))

def get_item(item_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return _item(row) if row else None

def create_digest(item_ids: Iterable[str], trending_ids: Iterable[str]) -> int:
    with connection() as conn:
        cur = conn.execute("INSERT INTO digests(run_date,item_ids,trending_ids) VALUES(?,?,?)",
          (date.today().isoformat(), _dump(list(item_ids)), _dump(list(trending_ids))))
        return int(cur.lastrowid)

def get_latest_digest() -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM digests ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None

def get_items_for_week(run_date: str | None = None) -> list[dict[str, Any]]:
    digest = get_latest_digest() if run_date is None else None
    if run_date is not None:
        with connection() as conn: digest = conn.execute("SELECT * FROM digests WHERE run_date=? ORDER BY id DESC LIMIT 1", (run_date,)).fetchone()
        digest = dict(digest) if digest else None
    if not digest: return []
    ids = json.loads(digest["item_ids"] or "[]") + json.loads(digest["trending_ids"] or "[]")
    if not ids: return []
    with connection() as conn:
        rows = conn.execute(f"SELECT * FROM items WHERE id IN ({','.join('?' for _ in ids)})", ids).fetchall()
    by_id = {r["id"]: _item(r) for r in rows}
    return [by_id[i] for i in ids if i in by_id]

def get_history(search: str = "", status: str | None = None) -> list[dict[str, Any]]:
    sql, args = "SELECT * FROM items WHERE 1=1", []
    if search: sql += " AND (title LIKE ? OR authors LIKE ? OR source LIKE ?)"; args += [f"%{search}%"] * 3
    if status and status != "All": sql += " AND status=?"; args.append(status)
    sql += " ORDER BY discovered_date DESC, relevance_score DESC"
    with connection() as conn: rows = conn.execute(sql, args).fetchall()
    return [_item(row) for row in rows]

def get_coverage_stats(window_days: int | None = None) -> dict[str, list[dict[str, Any]]]:
    """Promotion coverage using min(global lookback, days since an entry was added)."""
    config = load_config(); days = window_days or config["lookback_days"]; today = date.today()
    result: dict[str, list[dict[str, Any]]] = {}
    table = {"research_areas": "topics", "universities": "universities", "researchers": "researchers"}
    with connection() as conn:
        for section, column in table.items():
            records = []
            for entry in config[section]:
                added = date.fromisoformat(str(entry["date_added"])); effective = min(days, max(0, (today - added).days))
                start = (today - timedelta(days=effective)).isoformat()
                rows = conn.execute(f"SELECT promoted_date FROM items WHERE status='promoted' AND {column} LIKE ? AND promoted_date >= ?", (f'%"{entry["name"]}"%', start)).fetchall()
                records.append({"name": entry["name"], "date_added": added.isoformat(), "window_days": effective, "promotions": len(rows), "blind_spot": effective > 0 and len(rows) == 0})
            result[section] = records
    return result

def get_promotions_by_area() -> list[dict[str, Any]]:
    """Return promotion events for the Trends chart; JSON decoding stays in this data layer."""
    with connection() as conn:
        rows = conn.execute("SELECT promoted_date, topics FROM items WHERE status='promoted' AND promoted_date IS NOT NULL ORDER BY promoted_date").fetchall()
    return [{"date": row["promoted_date"], "topics": json.loads(row["topics"] or "[]")} for row in rows]

def item_tags(item: dict[str, Any]) -> list[str]:
    """Tags exported to Zotero; topic coverage remains separate in ``topics``."""
    ordered = item.get("questions", []) + item.get("topics", []) + item.get("universities", []) + item.get("researchers", [])
    return list(dict.fromkeys(tag for tag in ordered if tag))
