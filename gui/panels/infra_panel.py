import tkinter as tk
from tkinter import ttk, Menu

class InfraPanel(ttk.Frame):
    def __init__(self, parent, callbacks):
        super().__init__(parent)
        self.cb = callbacks
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar
        f_tools = ttk.Frame(self)
        f_tools.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(f_tools, text="📂 Lista TXT", command=self.cb['load_ips']).pack(side="left", padx=2)
        ttk.Button(f_tools, text="🏢 Dedicados CSV", command=self.cb['load_csv']).pack(side="left", padx=2)
        ttk.Button(f_tools, text="🛠️ Migrar Agente", command=self.cb['deploy']).pack(side="right", padx=2)

        # Tabela (Selectmode=extended para permitir Ctrl+Click)
        cols = ("IP", "Status", "Cliente", "Info")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="extended")
        
        self.tree.heading("IP", text="IP")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Cliente", text="Cliente")
        self.tree.heading("Info", text="Info")
        
        self.tree.column("IP", width=110, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Cliente", width=200, anchor="w")
        self.tree.column("Info", width=150, anchor="w")

        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5)
        scrolly.grid(row=1, column=1, sticky="ns")

        # Tags
        self.tree.tag_configure("ONLINE", background="#dff9fb")
        self.tree.tag_configure("OFFLINE", background="#ffcccc")
        self.tree.tag_configure("SUCESSO", background="#b8e994")
        self.tree.tag_configure("CRITICO", background="#e74c3c", foreground="white")
        self.tree.tag_configure("DEDICADO", background="#fff0b3")

        # Menu Contexto
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="🖥️ Acessar RDP", command=self.call_rdp)
        self.menu.add_command(label="📋 Copiar IP", command=self.copy_ip)
        self.tree.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            # Se clicou em algo fora da seleção atual, seleciona só ele
            # Se clicou dentro de um grupo já selecionado, mantém o grupo (útil para ações em lote futuras)
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def call_rdp(self):
        # Abre RDP apenas para o primeiro da seleção (não dá pra abrir 50 RDPs de vez)
        sel = self.tree.selection()
        if sel: self.cb['rdp'](self.tree.item(sel[0])['values'][0])

    def copy_ip(self):
        sel = self.tree.selection()
        if sel:
            ip = self.tree.item(sel[0])['values'][0]
            self.clipboard_clear()
            self.clipboard_append(ip)