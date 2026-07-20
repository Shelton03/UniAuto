from __future__ import annotations
import os, subprocess, sys, threading
from pathlib import Path
import customtkinter as ctk
from gui.widgets.log_console import LogConsole

ROOT=Path(__file__).resolve().parents[2]
class RunNowTab(ctk.CTkFrame):
    def __init__(self, master, on_finished=None, **kwargs):
        super().__init__(master, **kwargs); self.on_finished=on_finished
        self.run_button=ctk.CTkButton(self,text="Run weekly update now",command=self.start); self.run_button.pack(anchor="w",padx=14,pady=(14,8))
        self.status=ctk.CTkLabel(self,text="Ready."); self.status.pack(anchor="w",padx=14,pady=(0,8))
        self.console=LogConsole(self); self.console.pack(fill="both",expand=True,padx=14,pady=(0,14))
    def start(self):
        self.run_button.configure(state="disabled"); self.status.configure(text="Running discovery in the background..."); self.console.clear()
        threading.Thread(target=self._worker,daemon=True).start()
    def _worker(self):
        environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        process=subprocess.Popen([sys.executable,"-u",str(ROOT/"automation"/"weekly_update.py")],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",env=environment)
        for line in process.stdout: self.console.write(line)
        result=process.wait(); self.after(0,lambda:self._done(result))
    def _done(self,result):
        self.run_button.configure(state="normal"); self.status.configure(text="Update completed." if result==0 else f"Update failed (exit {result}).")
        if result==0 and self.on_finished: self.on_finished()
