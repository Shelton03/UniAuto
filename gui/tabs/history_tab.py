from __future__ import annotations

import tkinter.ttk as ttk

import customtkinter as ctk

from automation import state_store


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        header = ctk.CTkFrame(self, fg_color="#1d2c42", corner_radius=13)
        header.pack(fill="x", padx=14, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Discovery history", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        self.count = ctk.CTkLabel(header, text="", text_color="#aebbd0", anchor="w")
        self.count.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
        self.search = ctk.CTkEntry(header, placeholder_text="Search title, author, or source", width=300, height=34, fg_color="#111a29", border_color="#314866")
        self.search.grid(row=0, column=1, rowspan=2, padx=14, pady=14)
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Research.Treeview", background="#162236", fieldbackground="#162236", foreground="#dce8f7", rowheight=31, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Research.Treeview.Heading", background="#223650", foreground="#b9d5ff", relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Research.Treeview", background=[("selected", "#315d98")], foreground=[("selected", "#ffffff")])
        columns = ("discovered", "title", "source", "score", "status", "zotero", "obsidian")
        shell = ctk.CTkFrame(self, fg_color="#141f30", corner_radius=13)
        shell.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tree = ttk.Treeview(shell, columns=columns, show="headings", style="Research.Treeview")
        for column, width in zip(columns, (100, 440, 120, 65, 100, 75, 85)):
            self.tree.heading(column, text=column.title())
            self.tree.column(column, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        items = state_store.get_history(self.search.get().strip())
        self.count.configure(text=f"{len(items)} logged discoveries, including dismissed and promoted items.")
        for item in items:
            self.tree.insert("", "end", values=(item["discovered_date"], item["title"], item["source"], f"{item.get('relevance_score') or 0:g}", item["status"], "yes" if item.get("zotero_key") else "", "yes" if item.get("obsidian_path") else ""))
