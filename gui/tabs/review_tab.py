from __future__ import annotations

import threading
import webbrowser
from collections import Counter, defaultdict

import customtkinter as ctk

from automation import state_store
from automation.obsidian_push import push_to_obsidian
from automation.zotero_push import push_to_zotero

TRENDING_SOURCES = {"duckduckgo", "google_news"}
SOURCE_LABELS = {"arxiv": "arXiv", "openalex": "OpenAlex", "semantic_scholar": "Semantic Scholar", "rss": "Lab / university news"}
SOURCE_ORDER = tuple(SOURCE_LABELS)


class ReviewTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.notice = ctk.CTkLabel(self, text="", justify="left", anchor="w", wraplength=900)
        self.notice.pack(fill="x", padx=16, pady=(10, 0))
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs.add("Ranked discoveries")
        self.tabs.add("Trending topics")
        self.ranked_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Ranked discoveries"), label_text="Personalised papers and lab news")
        self.trending_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Trending topics"), label_text="Current AI topics and source coverage")
        self.ranked_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.trending_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh()

    def _set_notice(self, text: str, error: bool = False) -> None:
        self.notice.configure(text=text, text_color="salmon" if error else "pale green")

    def refresh(self):
        for scroll in (self.ranked_scroll, self.trending_scroll):
            for child in scroll.winfo_children():
                child.destroy()
        items = [item for item in state_store.get_items_for_week() if item["status"] != "dismissed"]
        regular = sorted((item for item in items if item["source"] not in TRENDING_SOURCES and item.get("review_eligible", 1)), key=lambda item: item.get("relevance_score") or 0, reverse=True)
        trending = [item for item in items if item["source"] == "google_news"]
        legacy_count = sum(item["source"] == "duckduckgo" for item in items)

        if regular:
            ctk.CTkLabel(self.ranked_scroll, text=f"{len(regular)} ranked discoveries", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=8, pady=(8, 2))
            source_counts = Counter(item["source"] for item in regular)
            summary = "  •  ".join(f"{SOURCE_LABELS[source]}: {source_counts[source]}" for source in SOURCE_ORDER)
            ctk.CTkLabel(self.ranked_scroll, text="Source coverage: " + summary, text_color="gray70", justify="left", anchor="w", wraplength=850).pack(anchor="w", padx=8, pady=(0, 8))
            for source in SOURCE_ORDER:
                source_items = [item for item in regular if item["source"] == source]
                if not source_items:
                    continue
                ctk.CTkLabel(self.ranked_scroll, text=f"{SOURCE_LABELS[source]} ({len(source_items)})", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=8, pady=(8, 2))
                for item in source_items:
                    self._card(item, self.ranked_scroll)
        else:
            ctk.CTkLabel(self.ranked_scroll, text="No ranked discoveries in this digest.").pack(padx=12, pady=12)

        if legacy_count:
            ctk.CTkLabel(self.trending_scroll, text="Your previous digest contains old category-page results. Run a new update to replace them with grouped article topics.", justify="left", wraplength=850, text_color="khaki").pack(anchor="w", padx=10, pady=(8, 4))
        if not trending:
            ctk.CTkLabel(self.trending_scroll, text="No current topic groups yet. Run a weekly update to collect current article headlines.").pack(padx=12, pady=12)
            return

        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in trending:
            grouped[item.get("trend_topic") or item["title"]].append(item)
        ordered_groups = sorted(grouped.items(), key=lambda pair: (-max(float(item.get("trend_score") or 0) for item in pair[1]), pair[0]))
        ctk.CTkLabel(self.trending_scroll, text=f"{len(ordered_groups)} current topics from {len(trending)} articles", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=8, pady=(8, 2))
        for topic, articles in ordered_groups:
            score = max(float(item.get("trend_score") or 0) for item in articles)
            outlets = {item.get("authors", ["Unknown source"])[0] for item in articles}
            group = ctk.CTkFrame(self.trending_scroll)
            group.pack(fill="x", padx=6, pady=7)
            heading = ctk.CTkFrame(group, fg_color="transparent")
            heading.pack(fill="x", padx=10, pady=(8, 1))
            ctk.CTkLabel(heading, text=topic, font=ctk.CTkFont(size=15, weight="bold"), justify="left", anchor="w", wraplength=720).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(heading, text=f"Trend score {score:g}", fg_color="#245b89", corner_radius=8).pack(side="right", padx=(8, 0))
            ctk.CTkLabel(group, text=f"{len(articles)} report(s) from {len(outlets)} site(s)  •  score = reports + 2 × distinct sites", text_color="gray70", justify="left", anchor="w", wraplength=820).pack(fill="x", padx=10, pady=(0, 2))
            for item in articles:
                self._card(item, group, compact=True)

    def _card(self, item, parent, compact: bool = False):
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=8, pady=5)
        card.grid_columnconfigure(0, weight=1)
        source = item.get("authors", [])
        byline = " • ".join(filter(None, [", ".join(source), item.get("source", ""), f"relevance {item.get('relevance_score', 0):g}" if not compact else ""]))
        ctk.CTkLabel(card, text=item["title"], font=ctk.CTkFont(size=14, weight="bold"), wraplength=830, justify="left", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 1))
        ctk.CTkLabel(card, text=byline, text_color="gray70", anchor="w", justify="left", wraplength=830).grid(row=1, column=0, sticky="ew", padx=10)
        tags = state_store.item_tags(item)
        detail_row = 2
        if tags:
            ctk.CTkLabel(card, text="Matched tags: " + "  •  ".join(tags), text_color="#91b9d8", anchor="w", justify="left", wraplength=830).grid(row=detail_row, column=0, sticky="ew", padx=10, pady=(2, 0))
            detail_row += 1
        if item.get("abstract") and not compact:
            ctk.CTkLabel(card, text=item["abstract"][:700], wraplength=830, justify="left", anchor="w").grid(row=detail_row, column=0, sticky="ew", padx=10, pady=(5, 2))
            detail_row += 1
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=detail_row, column=0, sticky="w", padx=8, pady=8)
        zotero_text = "In Zotero" if item.get("zotero_key") else "Add to Zotero"
        obsidian_text = "In Obsidian" if item.get("obsidian_path") else "Add to Obsidian"
        zotero = ctk.CTkButton(actions, text=zotero_text, width=118, state="disabled" if item.get("zotero_key") else "normal")
        obsidian = ctk.CTkButton(actions, text=obsidian_text, width=125, state="disabled" if item.get("obsidian_path") else "normal")
        visit = ctk.CTkButton(actions, text="Visit source", width=105, command=lambda url=item.get("url", ""): self._visit(url))
        dismiss = ctk.CTkButton(actions, text="Dismiss", width=80, fg_color="#8b3a3a", command=lambda: self._dismiss(item["id"]))
        zotero.configure(command=lambda: self._push(item["id"], push_to_zotero, zotero, "Zotero"))
        obsidian.configure(command=lambda: self._push(item["id"], push_to_obsidian, obsidian, "Obsidian"))
        zotero.grid(row=0, column=0, padx=2); obsidian.grid(row=0, column=1, padx=2); visit.grid(row=0, column=2, padx=2); dismiss.grid(row=0, column=3, padx=2)

    def _visit(self, url: str) -> None:
        if not url:
            self._set_notice("This discovery does not include a source URL.", error=True)
            return
        webbrowser.open_new_tab(url)

    def _dismiss(self, item_id: str):
        state_store.mark_dismissed(item_id)
        self._set_notice("Dismissed. It remains recorded in History.")
        self.refresh()

    def _push(self, item_id, operation, button, destination):
        button.configure(state="disabled")
        self._set_notice(f"Sending item to {destination}...")
        def worker():
            try:
                operation(item_id)
                message, failed = f"Added to {destination}.", False
            except Exception as exc:
                message, failed = f"{destination} could not be completed: {exc}", True
            self.after(0, lambda: self._finish_push(message, failed, button))
        threading.Thread(target=worker, daemon=True).start()

    def _finish_push(self, message: str, failed: bool, button) -> None:
        self._set_notice(message, error=failed)
        if failed:
            button.configure(state="normal")
        else:
            self.refresh()
