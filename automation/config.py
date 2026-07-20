from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
TRACKED_SECTIONS = ("research_questions", "research_areas", "universities", "researchers")
DEFAULTS = {
    "research_questions": [], "research_areas": [], "universities": [], "researchers": [],
    "sources": {"arxiv": True, "openalex": True, "semantic_scholar": True, "university_rss": True, "duckduckgo_trending": True},
    "lookback_days": 90, "zotero": {"collection_name": "00 Inbox"},
    "obsidian": {"vault_path": "", "landing_folder": "AutoLanding"},
}

def _validate(config: dict[str, Any]) -> dict[str, Any]:
    for section in TRACKED_SECTIONS:
        entries = config.get(section, [])
        if not isinstance(entries, list):
            raise ValueError(f"config.{section} must be a list")
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("name") or not entry.get("date_added"):
                raise ValueError(f"Every {section} entry needs name and date_added")
            try:
                date.fromisoformat(str(entry["date_added"]))
            except ValueError as exc:
                raise ValueError(f"Invalid date_added for {entry['name']}: {entry['date_added']}") from exc
    config["lookback_days"] = max(1, int(config.get("lookback_days", 90)))
    return config

def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    merged = {**DEFAULTS, **data}
    merged["sources"] = {**DEFAULTS["sources"], **(data.get("sources") or {})}
    merged["zotero"] = {**DEFAULTS["zotero"], **(data.get("zotero") or {})}
    merged["obsidian"] = {**DEFAULTS["obsidian"], **(data.get("obsidian") or {})}
    return _validate(merged)

def save_config(config: dict[str, Any], path: Path = CONFIG_PATH) -> None:
    _validate(config)
    path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

def names(config: dict[str, Any], section: str) -> list[str]:
    return [str(entry["name"]) for entry in config.get(section, [])]
