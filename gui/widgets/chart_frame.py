from __future__ import annotations
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ChartFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs): super().__init__(master, **kwargs); self.canvas = None
    def set_figure(self, figure) -> None:
        if self.canvas: self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(figure, master=self)
        self.canvas.draw(); self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
