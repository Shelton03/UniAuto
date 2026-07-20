from __future__ import annotations
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import customtkinter as ctk
from automation import state_store
from gui.widgets.chart_frame import ChartFrame

class TrendsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs); self.chart=ChartFrame(self); self.chart.pack(fill="both",expand=True,padx=12,pady=(12,4)); self.blind=ctk.CTkScrollableFrame(self,label_text="Possible blind spots"); self.blind.pack(fill="both",expand=True,padx=12,pady=(4,12)); self.refresh()
    def refresh(self):
        events=state_store.get_promotions_by_area(); by_date=defaultdict(Counter); topics=set()
        for event in events:
            for topic in event["topics"]: by_date[event["date"]][topic]+=1; topics.add(topic)
        fig,ax=plt.subplots(figsize=(8,3.6)); dates=sorted(by_date)
        if dates:
            bottoms=[0]*len(dates)
            for topic in sorted(topics):
                values=[by_date[d][topic] for d in dates]; ax.bar(dates,values,bottom=bottoms,label=topic); bottoms=[a+b for a,b in zip(bottoms,values)]
            ax.legend(fontsize=8); ax.set_ylabel("Promoted items"); ax.set_xlabel("Promotion date"); ax.tick_params(axis="x",rotation=35)
        else: ax.text(.5,.5,"No promoted items yet",ha="center",va="center"); ax.set_axis_off()
        fig.tight_layout(); self.chart.set_figure(fig); plt.close(fig)
        for child in self.blind.winfo_children(): child.destroy()
        coverage=state_store.get_coverage_stats()
        spots=[(label[:-1].replace("_"," ").title(),rec) for label,records in coverage.items() for rec in records if rec["blind_spot"]]
        if not spots: ctk.CTkLabel(self.blind,text="No age-eligible blind spots right now. New entries are intentionally excluded on their first day.").pack(anchor="w",padx=10,pady=8)
        for category,record in spots:
            row=ctk.CTkFrame(self.blind); row.pack(fill="x",padx=7,pady=3)
            ctk.CTkLabel(row,text=f"{category}: {record['name']} (0 promotions / {record['window_days']} days)").pack(side="left",padx=8,pady=5)
            ctk.CTkLabel(row,text="Needs attention",fg_color="#934343",corner_radius=8).pack(side="right",padx=8,pady=5)
