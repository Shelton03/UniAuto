from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import customtkinter as ctk
from gui.tabs.config_tab import ConfigTab
from gui.tabs.run_now_tab import RunNowTab
from gui.tabs.review_tab import ReviewTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.trends_tab import TrendsTab

class ResearchOS(ctk.CTk):
    def __init__(self):
        super().__init__(); self.title("Research OS"); self.geometry("1040x760"); self.minsize(850,600)
        ctk.set_appearance_mode("system"); ctk.set_default_color_theme("blue")
        tabs=ctk.CTkTabview(self); tabs.pack(fill="both",expand=True,padx=10,pady=10)
        names=["Config","Run now","Review","History","Trends"]
        for name in names: tabs.add(name)
        self.config_tab=ConfigTab(tabs.tab("Config"), on_saved=self.refresh_data); self.config_tab.pack(fill="both",expand=True)
        self.review_tab=ReviewTab(tabs.tab("Review")); self.review_tab.pack(fill="both",expand=True)
        self.history_tab=HistoryTab(tabs.tab("History")); self.history_tab.pack(fill="both",expand=True)
        self.trends_tab=TrendsTab(tabs.tab("Trends")); self.trends_tab.pack(fill="both",expand=True)
        self.run_tab=RunNowTab(tabs.tab("Run now"),on_finished=self.refresh_data); self.run_tab.pack(fill="both",expand=True)
    def refresh_data(self):
        self.review_tab.refresh(); self.history_tab.refresh(); self.trends_tab.refresh()

if __name__=="__main__": ResearchOS().mainloop()
