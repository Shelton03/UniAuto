from __future__ import annotations
import queue
import customtkinter as ctk

class LogConsole(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#101827", corner_radius=12, **kwargs); self.queue: queue.Queue[str] = queue.Queue()
        self.text = ctk.CTkTextbox(self, state="disabled", wrap="word", fg_color="#0b1220", text_color="#c9d7ea", font=ctk.CTkFont(family="Consolas", size=12))
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
