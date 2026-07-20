from __future__ import annotations

from datetime import date

import customtkinter as ctk

from automation.config import load_config, save_config

SECTIONS = ("research_questions", "research_areas", "universities", "researchers")
LABELS = {"research_questions": "Research questions", "research_areas": "Research areas", "universities": "Universities", "researchers": "Researchers"}
HINTS = {"research_questions": "What you want to understand", "research_areas": "Fields that should shape discovery", "universities": "Tag matched affiliations; never broaden search", "researchers": "People whose work you want to follow"}


class ConfigTab(ctk.CTkFrame):
    def __init__(self, master, on_saved=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = load_config()
        self.on_saved = on_saved
        self._build()

    def _build(self):
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Shape your research radar", font=ctk.CTkFont(size=20, weight="bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 0))
        ctk.CTkLabel(self, text="New entries are date-stamped automatically. They apply on your next discovery run.", text_color="#aebbd0", anchor="w").grid(row=0, column=0, columnspan=2, sticky="sw", padx=16, pady=(0, 12))

        lists = ctk.CTkScrollableFrame(self, label_text="TRACKED INTERESTS", fg_color="#141f30", label_fg_color="#1d2c42")
        lists.grid(row=1, column=0, sticky="nsew", padx=(14, 7), pady=(0, 14))
        for section in SECTIONS:
            frame = ctk.CTkFrame(lists, fg_color="#1b2a40", corner_radius=12)
            frame.pack(fill="x", padx=7, pady=7)
            ctk.CTkLabel(frame, text=LABELS[section], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=11, pady=(10, 0))
            ctk.CTkLabel(frame, text=HINTS[section], text_color="#aebbd0", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=11, pady=(0, 5))
            self._render_section(frame, section)

        options = ctk.CTkFrame(self, fg_color="#1b2a40", corner_radius=14)
        options.grid(row=1, column=1, sticky="nsew", padx=(7, 14), pady=(0, 14))
        ctk.CTkLabel(options, text="Sources and destinations", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=16, pady=(16, 1))
        ctk.CTkLabel(options, text="Choose what to collect and where manual promotions land.", text_color="#aebbd0", wraplength=360, justify="left").pack(anchor="w", padx=16, pady=(0, 12))
        self.source_vars = {name: ctk.BooleanVar(value=value) for name, value in self.config["sources"].items()}
        source_labels = {"duckduckgo_trending": "Current trending news"}
        for name, var in self.source_vars.items():
            ctk.CTkCheckBox(options, text=source_labels.get(name, name.replace("_", " ").title()), variable=var, fg_color="#3b78d8", hover_color="#4f8cff").pack(anchor="w", padx=16, pady=4)
        self._field(options, "Blind-spot lookback days", "lookback", str(self.config["lookback_days"]))
        self._field(options, "Zotero collection", "collection", self.config["zotero"]["collection_name"])
        self._field(options, "Obsidian vault path", "vault", self.config["obsidian"]["vault_path"])
        self._field(options, "Obsidian landing folder", "landing", self.config["obsidian"]["landing_folder"])
        self.status = ctk.CTkLabel(options, text="", justify="left", anchor="w", wraplength=340)
        self.status.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkButton(options, text="Save configuration", command=self.save, height=35, fg_color="#3b78d8", hover_color="#4f8cff", font=ctk.CTkFont(weight="bold")).pack(anchor="e", padx=16, pady=(4, 16))

    def _field(self, parent, label, attribute, value):
        ctk.CTkLabel(parent, text=label, text_color="#c9d7ea", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(13, 3))
        field = ctk.CTkEntry(parent, height=32, fg_color="#111a29", border_color="#314866")
        field.insert(0, value)
        field.pack(fill="x", padx=16)
        setattr(self, attribute, field)

    def _render_section(self, frame, section):
        rows = ctk.CTkFrame(frame, fg_color="transparent")
        rows.pack(fill="x", padx=9)
        for entry in self.config[section]:
            row = ctk.CTkFrame(rows, fg_color="#162236", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=entry["name"], anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", fill="x", expand=True, padx=(9, 4), pady=6)
            ctk.CTkLabel(row, text=entry["date_added"], text_color="#9eb4cf", fg_color="#243852", corner_radius=7, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
            ctk.CTkButton(row, text="Remove", width=62, height=25, fg_color="#5f3642", hover_color="#794553", command=lambda e=entry, s=section: self.remove(s, e)).pack(side="right", padx=5)
        add = ctk.CTkFrame(frame, fg_color="transparent")
        add.pack(fill="x", padx=9, pady=(7, 10))
        field = ctk.CTkEntry(add, placeholder_text=f"Add {LABELS[section][:-1].lower()}", height=31, fg_color="#111a29", border_color="#314866")
        field.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(add, text="Add", width=58, height=31, fg_color="#2f76c4", hover_color="#3f8fe4", command=lambda s=section, f=field: self.add(s, f)).pack(side="left", padx=(6, 0))

    def _rebuild(self):
        for child in self.winfo_children():
            child.destroy()
        self._build()

    def add(self, section, field):
        name = field.get().strip()
        if name and name.casefold() not in {entry["name"].casefold() for entry in self.config[section]}:
            self.config[section].append({"name": name, "date_added": date.today().isoformat()})
            self._rebuild()

    def remove(self, section, entry):
        self.config[section].remove(entry)
        self._rebuild()

    def save(self):
        try:
            self.config["sources"] = {name: var.get() for name, var in self.source_vars.items()}
            self.config["lookback_days"] = int(self.lookback.get())
            self.config["zotero"] = {"collection_name": self.collection.get().strip()}
            self.config["obsidian"] = {"vault_path": self.vault.get().strip(), "landing_folder": self.landing.get().strip()}
            save_config(self.config)
            self.status.configure(text="Saved. Your next update will use these interests.", text_color="#b8ebc8")
            if self.on_saved:
                self.on_saved()
        except Exception as exc:
            self.status.configure(text=f"Could not save: {exc}", text_color="#ffb4b4")
