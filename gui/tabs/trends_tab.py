from __future__ import annotations

from collections import Counter, defaultdict

import customtkinter as ctk
import matplotlib.pyplot as plt

from automation import state_store
from gui.widgets.chart_frame import ChartFrame


class TrendsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        header = ctk.CTkFrame(self, fg_color="#1d2c42", corner_radius=13)
        header.pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(header, text="Reading coverage", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(header, text="Promotions reveal where your attention is landing - and what may be underexplored.", text_color="#aebbd0", anchor="w").pack(anchor="w", padx=14, pady=(0, 12))
        self.chart = ChartFrame(self, fg_color="#141f30", corner_radius=13)
        self.chart.pack(fill="both", expand=True, padx=14, pady=(0, 7))
        self.blind = ctk.CTkScrollableFrame(self, label_text="POSSIBLE BLIND SPOTS", fg_color="#141f30", label_fg_color="#1d2c42")
        self.blind.pack(fill="both", expand=True, padx=14, pady=(7, 14))
        self.refresh()

    def refresh(self):
        events = state_store.get_promotions_by_area()
        by_date, topics = defaultdict(Counter), set()
        for event in events:
            for topic in event["topics"]:
                by_date[event["date"]][topic] += 1
                topics.add(topic)
        fig, axis = plt.subplots(figsize=(8, 3.6), facecolor="#141f30")
        axis.set_facecolor("#141f30")
        dates = sorted(by_date)
        if dates:
            bottoms = [0] * len(dates)
            palette = ["#4f8cff", "#6f65c7", "#3f9d7a", "#d18a49", "#bf5f45"]
            for index, topic in enumerate(sorted(topics)):
                values = [by_date[current_date][topic] for current_date in dates]
                axis.bar(dates, values, bottom=bottoms, label=topic, color=palette[index % len(palette)], width=0.58)
                bottoms = [lower + value for lower, value in zip(bottoms, values)]
            axis.legend(fontsize=8, facecolor="#1b2a40", edgecolor="#314866", labelcolor="#dce8f7", loc="upper left")
            axis.set_ylabel("Promoted items", color="#aebbd0")
            axis.set_xlabel("Promotion date", color="#aebbd0")
            axis.tick_params(axis="x", colors="#aebbd0", rotation=30)
            axis.tick_params(axis="y", colors="#aebbd0")
            axis.grid(axis="y", color="#314866", alpha=.45, linewidth=.7)
            for spine in axis.spines.values():
                spine.set_visible(False)
        else:
            axis.text(.5, .55, "No promoted items yet", color="#dce8f7", ha="center", va="center", fontsize=15, fontweight="bold")
            axis.text(.5, .42, "Promote papers from Review to build your personal coverage view.", color="#aebbd0", ha="center", va="center", fontsize=10)
            axis.set_axis_off()
        fig.tight_layout(pad=1.4)
        self.chart.set_figure(fig)
        plt.close(fig)

        for child in self.blind.winfo_children():
            child.destroy()
        coverage = state_store.get_coverage_stats()
        spots = [(label[:-1].replace("_", " ").title(), record) for label, records in coverage.items() for record in records if record["blind_spot"]]
        if not spots:
            ctk.CTkLabel(self.blind, text="Everything is covered for now.", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(self.blind, text="New entries are intentionally excluded on their first day, so they are not falsely marked as blind spots.", text_color="#aebbd0", justify="left", wraplength=850).pack(anchor="w", padx=10, pady=(0, 10))
        for category, record in spots:
            row = ctk.CTkFrame(self.blind, fg_color="#1b2a40", corner_radius=9)
            row.pack(fill="x", padx=7, pady=4)
            ctk.CTkLabel(row, text=category.upper(), text_color="#aebbd0", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=10, pady=(7, 0))
            ctk.CTkLabel(row, text=record["name"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=(0, 8))
            ctk.CTkLabel(row, text=f"0 promotions / {record['window_days']} days", text_color="#ffb4b4", fg_color="#4c2830", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10, pady=(0, 8))
