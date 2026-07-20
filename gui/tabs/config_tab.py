from __future__ import annotations
from datetime import date
import customtkinter as ctk
from automation.config import load_config, save_config

SECTIONS = ("research_questions", "research_areas", "universities", "researchers")
LABELS = {"research_questions":"Research questions", "research_areas":"Research areas", "universities":"Universities", "researchers":"Researchers"}

class ConfigTab(ctk.CTkFrame):
    def __init__(self, master, on_saved=None, **kwargs):
        super().__init__(master, **kwargs); self.config = load_config(); self.on_saved = on_saved; self.entries = {}; self._build()
    def _build(self):
        self.grid_columnconfigure((0,1), weight=1); self.grid_rowconfigure(0, weight=1)
        lists = ctk.CTkScrollableFrame(self, label_text="Tracked interests")
        lists.grid(row=0, column=0, sticky="nsew", padx=(12,6), pady=12)
        for index, section in enumerate(SECTIONS):
            frame = ctk.CTkFrame(lists); frame.pack(fill="x", padx=6, pady=6)
            ctk.CTkLabel(frame, text=LABELS[section], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=8, pady=(6,2))
            self._render_section(frame, section)
        options = ctk.CTkFrame(self); options.grid(row=0, column=1, sticky="nsew", padx=(6,12), pady=12)
        ctk.CTkLabel(options, text="Sources and settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=12, pady=(12,5))
        self.source_vars = {name: ctk.BooleanVar(value=value) for name, value in self.config["sources"].items()}
        source_labels = {"duckduckgo_trending": "Current trending news"}
        for name, var in self.source_vars.items(): ctk.CTkCheckBox(options, text=source_labels.get(name, name.replace("_", " ").title()), variable=var).pack(anchor="w", padx=12, pady=3)
        ctk.CTkLabel(options, text="Blind-spot lookback days").pack(anchor="w", padx=12, pady=(16,2))
        self.lookback = ctk.CTkEntry(options); self.lookback.insert(0, str(self.config["lookback_days"])); self.lookback.pack(fill="x", padx=12)
        ctk.CTkLabel(options, text="Zotero collection").pack(anchor="w", padx=12, pady=(12,2))
        self.collection = ctk.CTkEntry(options); self.collection.insert(0, self.config["zotero"]["collection_name"]); self.collection.pack(fill="x", padx=12)
        ctk.CTkLabel(options, text="Obsidian vault path / landing folder").pack(anchor="w", padx=12, pady=(12,2))
        self.vault = ctk.CTkEntry(options); self.vault.insert(0, self.config["obsidian"]["vault_path"]); self.vault.pack(fill="x", padx=12, pady=2)
        self.landing = ctk.CTkEntry(options); self.landing.insert(0, self.config["obsidian"]["landing_folder"]); self.landing.pack(fill="x", padx=12, pady=2)
        self.status = ctk.CTkLabel(options, text="") ; self.status.pack(anchor="w", padx=12, pady=8)
        ctk.CTkButton(options, text="Save configuration", command=self.save).pack(anchor="e", padx=12, pady=12)
    def _render_section(self, frame, section):
        rows = ctk.CTkFrame(frame, fg_color="transparent"); rows.pack(fill="x", padx=8)
        for entry in self.config[section]:
            row = ctk.CTkFrame(rows); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{entry['name']}  ·  added {entry['date_added']}").pack(side="left", padx=7, pady=4)
            ctk.CTkButton(row, text="Remove", width=64, height=25, command=lambda e=entry, s=section: self.remove(s,e)).pack(side="right", padx=4)
        add = ctk.CTkFrame(frame, fg_color="transparent"); add.pack(fill="x", padx=8, pady=(5,8))
        field = ctk.CTkEntry(add, placeholder_text=f"Add {LABELS[section][:-1].lower()}"); field.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(add, text="Add", width=60, command=lambda s=section, f=field: self.add(s,f)).pack(side="left", padx=(5,0))
    def _rebuild(self):
        for child in self.winfo_children(): child.destroy()
        self._build()
    def add(self, section, field):
        name=field.get().strip()
        if name and name.casefold() not in {x["name"].casefold() for x in self.config[section]}:
            self.config[section].append({"name": name, "date_added": date.today().isoformat()}); self._rebuild()
    def remove(self, section, entry): self.config[section].remove(entry); self._rebuild()
    def save(self):
        try:
            self.config["sources"]={name: var.get() for name,var in self.source_vars.items()}; self.config["lookback_days"]=int(self.lookback.get())
            self.config["zotero"]={"collection_name":self.collection.get().strip()}; self.config["obsidian"]={"vault_path":self.vault.get().strip(), "landing_folder":self.landing.get().strip()}
            save_config(self.config); self.status.configure(text="Saved.", text_color="pale green")
            if self.on_saved: self.on_saved()
        except Exception as exc: self.status.configure(text=f"Could not save: {exc}", text_color="salmon")
