import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

class TopPanel(ttk.LabelFrame):
    def __init__(self, parent, core_callback_link_check):
        super().__init__(parent, text="1. Parâmetros da Missão", padding=10)
        self.core_link_check = core_callback_link_check
        self.setup_widgets()

    def setup_widgets(self):
        # Linha 0: Sistema e Tipo
        ttk.Label(self, text="Sistema:").grid(row=0, column=0, sticky="e")
        self.combo_sys = ttk.Combobox(self, values=["AC", "AG", "PONTO", "PATRIO"], width=10, state="readonly")
        self.combo_sys.current(0)
        self.combo_sys.grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self, text='Modo:').grid(row=0, column=2, sticky='e')
        self.combo_tipo = ttk.Combobox(self, values=["1 - Atualização Base (AWS)", "2 - Troca de EXE (Rede Local)"], width=28, state='readonly')
        self.combo_tipo.current(0)
        self.combo_tipo.grid(row=0, column=3, padx=5, sticky='w')
        self.combo_tipo.bind("<<ComboboxSelected>>", self.toggle_interface)

        # Linha 1: Link AWS e Status
        self.lbl_url = ttk.Label(self, text="Link AWS:")
        self.lbl_url.grid(row=1, column=0, sticky="e", pady=5)
        self.entry_url = ttk.Entry(self, width=60)
        self.entry_url.grid(row=1, column=1, columnspan=3, padx=5, sticky="ew")
        self.entry_url.bind("<KeyRelease>", self.on_link_check)
        self.entry_url.bind("<FocusOut>", self.on_link_check)
        
        self.lbl_status = tk.Label(self, text="", font=("Arial", 9, "bold")) 
        self.lbl_status.grid(row=1, column=4, sticky="w", padx=5)

        # Linha 2: Credenciais
        ttk.Label(self, text="User Task/RDP:").grid(row=2, column=0, sticky="e")
        self.entry_user = ttk.Entry(self, width=25)
        self.entry_user.insert(0, ".\\parceiro")
        self.entry_user.grid(row=2, column=1, padx=5, sticky="w")

        ttk.Label(self, text="Senha:").grid(row=2, column=2, sticky="e")
        self.entry_pass = ttk.Entry(self, width=20, show="*")
        self.entry_pass.grid(row=2, column=3, padx=5, sticky="w")

        # Linha 3: Data e Hora
        ttk.Label(self, text="Data:").grid(row=3, column=0, sticky="e")
        self.entry_date = ttk.Entry(self, width=12)
        self.entry_date.insert(0, (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"))
        self.entry_date.grid(row=3, column=1, padx=5, sticky='w')

        ttk.Label(self, text="Hora:").grid(row=3, column=2, sticky="e")
        self.entry_time = ttk.Entry(self, width=8)
        self.entry_time.insert(0, "03:00")
        self.entry_time.grid(row=3, column=3, padx=5, sticky="w")
        
        ttk.Label(self, text="(+15min/lote)").grid(row=3, column=4, sticky="w")

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
            'sistema': self.combo_sys.get(),
            'tipo': self.combo_tipo.get(),
            'url': self.entry_url.get(),
            'user': self.entry_user.get(),
            'pass': self.entry_pass.get(),
            'data': self.entry_date.get(),
            'hora': self.entry_time.get()
        }