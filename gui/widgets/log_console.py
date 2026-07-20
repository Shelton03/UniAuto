from __future__ import annotations
import queue
import customtkinter as ctk

class LogConsole(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs); self.queue: queue.Queue[str] = queue.Queue()
        self.text = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.text.pack(fill="both", expand=True, padx=8, pady=8); self.after(80, self._drain)
    def write(self, message: str) -> None: self.queue.put(message)
    def clear(self) -> None:
        self.text.configure(state="normal"); self.text.delete("1.0", "end"); self.text.configure(state="disabled")
    def _drain(self) -> None:
        changed = False; self.text.configure(state="normal")
        while True:
            try: self.text.insert("end", self.queue.get_nowait()); changed = True
            except queue.Empty: break
        if changed: self.text.see("end")
        self.text.configure(state="disabled"); self.after(80, self._drain)
