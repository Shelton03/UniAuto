from __future__ import annotations
import os, subprocess, sys, threading
from pathlib import Path
import customtkinter as ctk
from gui.widgets.log_console import LogConsole

ROOT=Path(__file__).resolve().parents[2]
class RunNowTab(ctk.CTkFrame):
    def __init__(self, master, on_finished=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs); self.on_finished=on_finished
        hero = ctk.CTkFrame(self, fg_color="#1d2c42", corner_radius=14)
        hero.pack(fill="x", padx=14, pady=(14, 10))
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hero, text="Refresh your research radar", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=16, pady=(14, 1))
        ctk.CTkLabel(hero, text="Runs discovery in the background. Your window stays responsive and the live log appears below.", text_color="#aebbd0", anchor="w", wraplength=650).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
        self.run_button=ctk.CTkButton(hero,text="Run update",command=self.start, width=130, height=36, fg_color="#3b78d8", hover_color="#4f8cff", font=ctk.CTkFont(weight="bold")); self.run_button.grid(row=0, column=1, rowspan=2, padx=16, pady=16)
        self.status=ctk.CTkLabel(self,text="Ready to discover.", text_color="#aebbd0", anchor="w"); self.status.pack(fill="x", padx=18, pady=(0,6))
        self.console=LogConsole(self); self.console.pack(fill="both",expand=True,padx=14,pady=(0,14))
    def start(self):
        self.run_button.configure(state="disabled", text="Running..."); self.status.configure(text="Discovery is running in the background...", text_color="#8fb9ff"); self.console.clear()
        threading.Thread(target=self._worker,daemon=True).start()
    def _worker(self):
        environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        process=subprocess.Popen([sys.executable,"-u",str(ROOT/"automation"/"weekly_update.py")],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",env=environment)
        for line in process.stdout: self.console.write(line)
        result=process.wait(); self.after(0,lambda:self._done(result))
    def _done(self,result):
        self.run_button.configure(state="normal", text="Run update"); self.status.configure(text="Update completed. Review your new discoveries." if result==0 else f"Update failed (exit {result}).", text_color="#9bd3ae" if result==0 else "#f4a6a6")
        if result==0 and self.on_finished: self.on_finished()
