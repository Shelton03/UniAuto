from __future__ import annotations

import os
from dotenv import load_dotenv
from pyzotero import zotero
from automation.config import ROOT, load_config
from automation import state_store

load_dotenv(ROOT / ".env")

def _client() -> zotero.Zotero:
    api_key, user_id = os.getenv("ZOTERO_API_KEY"), os.getenv("ZOTERO_USER_ID")
    if not api_key or not user_id:
        raise RuntimeError("ZOTERO_API_KEY and ZOTERO_USER_ID must be set in .env")
    return zotero.Zotero(user_id, "user", api_key)

def _collection_key(client: zotero.Zotero, name: str) -> str:
    target = " ".join(name.split()).casefold()
    # all_collections() is a flat list containing nested collections too. That
    # is intentional: "My Library" is the library root, not a collection, and
    # 00 Inbox may sit at any collection depth below it.
    collections = client.all_collections()
    matches = [collection for collection in collections if " ".join(collection.get("data", {}).get("name", "").split()).casefold() == target]
    if len(matches) == 1:
        return matches[0].get("key") or matches[0]["data"]["key"]
    if len(matches) > 1:
        raise RuntimeError(f'More than one Zotero subcollection matches "{name}". Rename one so Research OS can safely choose the intended collection.')
    available = ", ".join(collection.get("data", {}).get("name", "") for collection in collections[:15])
    raise RuntimeError(f'Zotero collection "{name}" was not found at any depth below My Library. Available collections include: {available or "none"}.')

def push_to_zotero(item_id: str) -> str:
    """Create an item in the configured existing collection and record its Zotero key."""
    item = state_store.get_item(item_id)
    if not item: raise KeyError(f"Unknown item: {item_id}")
    if item.get("zotero_key"): return item["zotero_key"]
    client, config = _client(), load_config()
    collection_key = _collection_key(client, config["zotero"]["collection_name"])
    template = client.item_template("journalArticle")
    template.update({
        "title": item["title"], "DOI": item.get("doi", ""), "url": item.get("url", ""),
        "abstractNote": item.get("abstract", ""), "date": item.get("published_date", ""),
        "collections": [collection_key],
        "creators": [{"creatorType": "author", "name": author} for author in item.get("authors", [])],
        "tags": [{"tag": tag} for tag in state_store.item_tags(item)],
    })
    # A DOI is supplied when available, allowing Zotero clients to enrich the record; all metadata
    # is also mapped so the item remains useful when DOI lookup is unavailable.
    response = client.create_items([template])
    successful = response.get("success") or response.get("successful") or {}
    if not successful:
        raise RuntimeError(f"Zotero rejected the item: {response}")
    created = next(iter(successful.values()))
    key = created if isinstance(created, str) else created["key"]
    state_store.mark_promoted(item_id, zotero_key=key)
    return key
