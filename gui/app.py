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
        super().__init__()
        self.title("Research OS")
        self.geometry("1140x800")
        self.minsize(920, 650)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#101827")

        header = ctk.CTkFrame(self, fg_color="#172235", corner_radius=16)
        header.pack(fill="x", padx=16, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="R", width=42, height=42, corner_radius=12, fg_color="#4f8cff", font=ctk.CTkFont(size=21, weight="bold")).grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=14)
        ctk.CTkLabel(header, text="Research OS", font=ctk.CTkFont(size=24, weight="bold"), anchor="w").grid(row=0, column=1, sticky="sw", pady=(12, 0))
        ctk.CTkLabel(header, text="Personal research radar  |  Discover, review, and promote with intent", text_color="#aebbd0", anchor="w").grid(row=1, column=1, sticky="nw", pady=(0, 12))
        ctk.CTkLabel(header, text="LOCAL ONLY", fg_color="#203a59", text_color="#b9d5ff", corner_radius=9, font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, rowspan=2, padx=16, pady=18)

        tabs=ctk.CTkTabview(self, fg_color="#172235", corner_radius=16, segmented_button_fg_color="#111a29", segmented_button_selected_color="#3b78d8", segmented_button_selected_hover_color="#4f8cff", segmented_button_unselected_color="#111a29", segmented_button_unselected_hover_color="#23354f")
        tabs.pack(fill="both",expand=True,padx=16,pady=(0, 16))
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
