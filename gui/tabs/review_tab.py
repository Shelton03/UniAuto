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
SOURCE_COLORS = {"arxiv": "#bf5f45", "openalex": "#3579c8", "semantic_scholar": "#3f9d7a", "rss": "#8565bd", "google_news": "#b68a31"}


class ReviewTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.notice_box = ctk.CTkFrame(self, fg_color="#1c314a", corner_radius=10)
        self.notice_box.pack(fill="x", padx=14, pady=(14, 0))
        self.notice = ctk.CTkLabel(self.notice_box, text="Review actions and errors will appear here.", text_color="#b8cbe3", justify="left", anchor="w", wraplength=940)
        self.notice.pack(fill="x", padx=12, pady=8)
        self.tabs = ctk.CTkTabview(self, fg_color="#172235", corner_radius=14, segmented_button_fg_color="#101827", segmented_button_selected_color="#356fc3", segmented_button_selected_hover_color="#4f8cff", segmented_button_unselected_color="#101827", segmented_button_unselected_hover_color="#23354f")
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs.add("Ranked discoveries")
        self.tabs.add("Trending topics")
        self.ranked_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Ranked discoveries"), label_text="Personalised papers and lab news", fg_color="#141f30")
        self.trending_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Trending topics"), label_text="Current AI topics and source coverage", fg_color="#141f30")
        self.ranked_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.trending_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh()

    def _set_notice(self, text: str, error: bool = False) -> None:
        self.notice_box.configure(fg_color="#4c2830" if error else "#1e3b35")
        self.notice.configure(text=text, text_color="#ffb4b4" if error else "#b8ebc8")

    def refresh(self):
        for scroll in (self.ranked_scroll, self.trending_scroll):
            for child in scroll.winfo_children():
                child.destroy()
        items = [item for item in state_store.get_items_for_week() if item["status"] != "dismissed"]
        regular = sorted((item for item in items if item["source"] not in TRENDING_SOURCES and item.get("review_eligible", 1)), key=lambda item: item.get("relevance_score") or 0, reverse=True)
        unique_regular, seen_titles = [], set()
        for item in regular:
            key = " ".join(item["title"].casefold().split())
            if key not in seen_titles:
                unique_regular.append(item)
                seen_titles.add(key)
        regular = unique_regular
        trending = [item for item in items if item["source"] == "google_news"]
        legacy_count = sum(item["source"] == "duckduckgo" for item in items)

        if regular:
            overview = ctk.CTkFrame(self.ranked_scroll, fg_color="#20324a", corner_radius=12)
            overview.pack(fill="x", padx=6, pady=(8, 10))
            ctk.CTkLabel(overview, text=f"{len(regular)}", font=ctk.CTkFont(size=23, weight="bold"), text_color="#b9d5ff").pack(side="left", padx=(14, 6), pady=10)
            ctk.CTkLabel(overview, text="relevant discoveries ready to review", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(side="left", pady=10)
            source_counts = Counter(item["source"] for item in regular)
            summary = " | ".join(f"{SOURCE_LABELS[source]}: {source_counts[source]}" for source in SOURCE_ORDER)
            ctk.CTkLabel(self.ranked_scroll, text="Source coverage  |  " + summary, text_color="#aebbd0", justify="left", anchor="w", wraplength=850).pack(anchor="w", padx=10, pady=(0, 8))
            for source in SOURCE_ORDER:
                source_items = [item for item in regular if item["source"] == source]
                if not source_items:
                    continue
                section = ctk.CTkFrame(self.ranked_scroll, fg_color="transparent")
                section.pack(fill="x", padx=8, pady=(12, 3))
                ctk.CTkLabel(section, text=SOURCE_LABELS[source].upper(), text_color="#aebbd0", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
                ctk.CTkLabel(section, text=str(len(source_items)), fg_color=SOURCE_COLORS[source], corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"), width=28).pack(side="left", padx=8)
                for item in source_items:
                    self._card(item, self.ranked_scroll)
        else:
            ctk.CTkLabel(self.ranked_scroll, text="No ranked discoveries in this digest.", text_color="#aebbd0").pack(padx=12, pady=12)

        if legacy_count:
            ctk.CTkLabel(self.trending_scroll, text="Your previous digest contains old category-page results. Run an update to replace them with grouped article topics.", justify="left", wraplength=850, text_color="#ead98d").pack(anchor="w", padx=10, pady=(8, 4))
        if not trending:
            ctk.CTkLabel(self.trending_scroll, text="No current topic groups yet. Run a weekly update to collect current article headlines.", text_color="#aebbd0").pack(padx=12, pady=12)
            return

        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in trending:
            grouped[item.get("trend_topic") or item["title"]].append(item)
        ordered_groups = sorted(grouped.items(), key=lambda pair: (-max(float(item.get("trend_score") or 0) for item in pair[1]), pair[0]))
        ctk.CTkLabel(self.trending_scroll, text=f"{len(ordered_groups)} current topics", font=ctk.CTkFont(size=19, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self.trending_scroll, text=f"{len(trending)} reports grouped by coverage, not generic search pages.", text_color="#aebbd0").pack(anchor="w", padx=10, pady=(0, 5))
        for topic, articles in ordered_groups:
            score = max(float(item.get("trend_score") or 0) for item in articles)
            outlets = {item.get("authors", ["Unknown source"])[0] for item in articles}
            group = ctk.CTkFrame(self.trending_scroll, fg_color="#1b2a40", corner_radius=12)
            group.pack(fill="x", padx=6, pady=7)
            heading = ctk.CTkFrame(group, fg_color="transparent")
            heading.pack(fill="x", padx=10, pady=(8, 1))
            ctk.CTkLabel(heading, text=topic, font=ctk.CTkFont(size=15, weight="bold"), justify="left", anchor="w", wraplength=720).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(heading, text=f"SCORE {score:g}", fg_color="#245b89", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=(8, 0))
            ctk.CTkLabel(group, text=f"{len(articles)} reports from {len(outlets)} sites  |  score = reports + 2 x distinct sites", text_color="#aebbd0", justify="left", anchor="w", wraplength=820).pack(fill="x", padx=10, pady=(0, 2))
            for item in articles:
                self._card(item, group, compact=True)

    def _card(self, item, parent, compact: bool = False):
        card = ctk.CTkFrame(parent, fg_color="#1c2738", corner_radius=10)
        card.pack(fill="x", padx=8, pady=5)
        card.grid_columnconfigure(0, weight=1)
        heading = ctk.CTkFrame(card, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 1))
        heading.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(heading, text=item["title"], font=ctk.CTkFont(size=14, weight="bold"), wraplength=690, justify="left", anchor="w").grid(row=0, column=0, sticky="ew")
        source_key = item.get("source", "")
        ctk.CTkLabel(heading, text=SOURCE_LABELS.get(source_key, source_key).upper(), fg_color=SOURCE_COLORS.get(source_key, "#51647c"), corner_radius=8, font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=1, sticky="ne", padx=(10, 0))
        byline = ", ".join(item.get("authors", []))
        if not compact:
            byline = " | ".join(filter(None, [byline, f"relevance {item.get('relevance_score', 0):g}"]))
        ctk.CTkLabel(card, text=byline, text_color="#aebbd0", anchor="w", justify="left", wraplength=830).grid(row=1, column=0, sticky="ew", padx=10)
        tags = state_store.item_tags(item)
        detail_row = 2
        if tags:
            ctk.CTkLabel(card, text="MATCHED  " + " | ".join(tags), text_color="#8fb9ff", anchor="w", justify="left", wraplength=830, font=ctk.CTkFont(size=12, weight="bold")).grid(row=detail_row, column=0, sticky="ew", padx=10, pady=(4, 0))
            detail_row += 1
        if item.get("abstract") and not compact:
            ctk.CTkLabel(card, text=item["abstract"][:700], wraplength=830, justify="left", anchor="w", text_color="#d5deeb").grid(row=detail_row, column=0, sticky="ew", padx=10, pady=(5, 2))
            detail_row += 1
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=detail_row, column=0, sticky="w", padx=8, pady=8)
        zotero_text = "In Zotero" if item.get("zotero_key") else "Add to Zotero"
        obsidian_text = "In Obsidian" if item.get("obsidian_path") else "Add to Obsidian"
        zotero = ctk.CTkButton(actions, text=zotero_text, width=118, height=31, fg_color="#2f76c4", hover_color="#3f8fe4", state="disabled" if item.get("zotero_key") else "normal")
        obsidian = ctk.CTkButton(actions, text=obsidian_text, width=125, height=31, fg_color="#6656b3", hover_color="#7b6acb", state="disabled" if item.get("obsidian_path") else "normal")
        visit = ctk.CTkButton(actions, text="Visit source", width=105, height=31, fg_color="#28384f", hover_color="#364b68", command=lambda url=item.get("url", ""): self._visit(url))
        dismiss = ctk.CTkButton(actions, text="Dismiss", width=80, height=31, fg_color="#713b47", hover_color="#8a4b5a", command=lambda: self._dismiss(item["id"]))
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
