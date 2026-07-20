from __future__ import annotations

import re
from datetime import date
from pathlib import Path
import yaml
from automation.config import load_config
from automation import state_store

def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:120] or "untitled"

def push_to_obsidian(item_id: str) -> str:
    """Write only to the configured landing folder; it must already exist."""
    item = state_store.get_item(item_id)
    if not item: raise KeyError(f"Unknown item: {item_id}")
    if item.get("obsidian_path"): return item["obsidian_path"]
    config = load_config()["obsidian"]
    vault = Path(config.get("vault_path", ""))
    folder = vault / config.get("landing_folder", "")
    if not vault.is_dir(): raise RuntimeError(f"Configured Obsidian vault does not exist: {vault}")
    if not folder.is_dir(): raise RuntimeError(f"Configured Obsidian landing folder does not exist: {folder}. Create it manually; Research OS will not alter vault structure.")
    path = folder / f"{date.today().isoformat()}-{_slug(item['title'])}.md"
    if path.exists(): path = folder / f"{date.today().isoformat()}-{_slug(item['title'])}-{item_id[-6:]}.md"
    links = lambda values: [f"[[{value}]]" for value in values]
    frontmatter = {
        "title": item["title"], "authors": item.get("authors", []), "doi": item.get("doi", ""), "url": item.get("url", ""),
        "tags": state_store.item_tags(item), "research_questions": links(item.get("questions", [])),
        "research_areas": links(item.get("topics", [])), "universities": links(item.get("universities", [])),
        "researchers": links(item.get("researchers", [])), "source": item.get("source", ""), "discovered": item.get("discovered_date", ""),
    }
    source_link = f"[Open source]({item.get('url')})" if item.get("url") else "No source URL available."
    content = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n## Source\n" + source_link + "\n\n## Abstract\n" + (item.get("abstract") or "") + "\n\n## My thoughts\n\n"
    path.write_text(content, encoding="utf-8")
    state_store.mark_promoted(item_id, obsidian_path=str(path))
    return str(path)
