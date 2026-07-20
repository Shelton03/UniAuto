from __future__ import annotations
import tkinter.ttk as ttk
import customtkinter as ctk
from automation import state_store

class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs); self.search=ctk.CTkEntry(self,placeholder_text="Search title, author, or source"); self.search.pack(fill="x",padx=12,pady=(12,5)); self.search.bind("<KeyRelease>",lambda _e:self.refresh())
        columns=("discovered","title","source","score","status","zotero","obsidian")
        self.tree=ttk.Treeview(self,columns=columns,show="headings")
        for column,width in zip(columns,(100,390,110,60,100,75,80)):
            self.tree.heading(column,text=column.title()); self.tree.column(column,width=width,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=12,pady=(5,12)); self.refresh()
    def refresh(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for item in state_store.get_history(self.search.get().strip()):
            self.tree.insert("","end",values=(item["discovered_date"],item["title"],item["source"],f"{item.get('relevance_score') or 0:g}",item["status"],"yes" if item.get("zotero_key") else "", "yes" if item.get("obsidian_path") else ""))
