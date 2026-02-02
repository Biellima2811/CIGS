import tkinter as tk
from tkinter import ttk, scrolledtext

class DbPanel(ttk.Frame):
    def __init__(self, parent, check_callback):
        super().__init__(parent)
        self.on_check = check_callback
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Barra de Ferramentas
        top = ttk.Frame(self, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(top, text="Ferramentas de Banco (Firebird/SQL)").pack(side="left")
        
        # Botões de Ação
        ttk.Button(top, text="🩺 1. Executar Check-up (Integridade)", command=self.on_check).pack(side="right", padx=5)
        ttk.Button(top, text="🧹 2. Limpeza (Sweep - Breve)", state="disabled").pack(side="right", padx=5)

        # Área de Log
        self.log_area = scrolledtext.ScrolledText(self, height=20, font=("Consolas", 9))
        self.log_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
    
    def clear(self):
        self.log_area.delete(1.0, tk.END)