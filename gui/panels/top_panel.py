import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

class TopPanel(ttk.LabelFrame):
    def __init__(self, parent, callback_link):
        super().__init__(parent, text="1. Parâmetros da Missão", padding=10)
        self.cb_link = callback_link
        self.setup_ui()

    def setup_ui(self):
       # Grid Configuration
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(5, weight=1)

        # Linha 0: URL
        ttk.Label(self, text="Link (AWS/S3):").grid(row=0, column=0, sticky="w")
        self.ent_url = ttk.Entry(self, width=50)
        self.ent_url.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5)
        self.ent_url.bind("<KeyRelease>", self.check_link)
        
        self.lbl_status_link = ttk.Label(self, text="⚪ Aguardando...", width=25)
        self.lbl_status_link.grid(row=0, column=4, columnspan=2, sticky="w")

        # Linha 1: Data, Hora, Credenciais
        ttk.Label(self, text="Data:").grid(row=1, column=0, sticky="w")
        self.ent_data = ttk.Entry(self, width=12)
        self.ent_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_data.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(self, text="Hora:").grid(row=1, column=2, sticky="e")
        self.ent_hora = ttk.Entry(self, width=8)
        self.ent_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.ent_hora.grid(row=1, column=3, sticky="w", padx=5)

        ttk.Label(self, text="User (Admin):").grid(row=1, column=4, sticky="e")
        self.ent_user = ttk.Entry(self, width=15)
        self.ent_user.insert(0, "Administrador")
        self.ent_user.grid(row=1, column=5, sticky="ew", padx=5)

        ttk.Label(self, text="Senha:").grid(row=1, column=6, sticky="e")
        self.ent_pass = ttk.Entry(self, show="*", width=15)
        self.ent_pass.grid(row=1, column=7, sticky="ew", padx=5)

        # Linha 2: Sistema e Script (NOVO - CIRÚRGICO)
        ttk.Label(self, text="Sistema:").grid(row=2, column=0, sticky="w", pady=5)
        self.cb_sis = ttk.Combobox(self, values=["AC", "AG", "PONTO", "PATRIO"], width=10, state="readonly")
        self.cb_sis.current(0)
        self.cb_sis.grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(self, text="Script Alvo:").grid(row=2, column=2, sticky="e")
        self.cb_script = ttk.Combobox(self, values=["Executa.bat", "ExecutaOnDemand.bat"], width=20)
        self.cb_script.current(0)
        self.cb_script.grid(row=2, column=3, sticky="w", padx=5)

        ttk.Label(self, text="Clientes/Args:").grid(row=2, column=4, sticky="e")
        self.ent_params = ttk.Entry(self, width=20) # Ex: 1,2,3 ou /silent
        self.ent_params.grid(row=2, column=5, columnspan=3, sticky="ew", padx=5)
        
        # Linha 3: Fonte (Local/Nuvem)
        ttk.Label(self, text="Fonte:").grid(row=3, column=0, sticky="w")
        self.cb_tipo = ttk.Combobox(self, values=["Nuvem (Link AWS)", "Rede Local (Cópia)"], state="readonly")
        self.cb_tipo.current(0)
        self.cb_tipo.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)
    
    def check_link(self, event=None):
        url = self.ent_url.get()
        if hasattr(self, 'cb_link'): # Proteção extra
            valid, msg, color = self.cb_link(url)
            self.lbl_status_link.config(text=msg, foreground=color)

    def toggle_interface(self, event):
        if "Rede Local" in self.combo_tipo.get():
            self.entry_url.config(state='disabled')
            self.lbl_status.config(text="Modo Local: Copiaremos da Central", fg="blue")
        else:
            self.entry_url.config(state='normal')
            self.lbl_status.config(text="")

    def on_link_check(self, event):
        url = self.entry_url.get()
        if not url or "Rede Local" in self.combo_tipo.get(): return
        valido, msg, cor = self.core_link_check(url)
        self.lbl_status.config(text=msg, fg=cor)

    def get_data(self):
        return {
            "url": self.ent_url.get().strip(),
            "data": self.ent_data.get().strip(),
            "hora": self.ent_hora.get().strip(),
            "user": self.ent_user.get().strip(),
            "pass": self.ent_pass.get().strip(),
            "sistema": self.cb_sis.get().strip(),
            "script": self.cb_script.get().strip(), # Enviando nome do script
            "params": self.ent_params.get().strip(), # Enviando parâmetros
            "tipo": self.cb_tipo.get()
        }