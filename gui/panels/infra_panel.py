# Importa o módulo principal do Tkinter para criar interfaces gráficas
import tkinter as tk
# Importa ttk (themed widgets) e Menu (menu de contexto)
from tkinter import ttk, Menu

# Classe que representa o painel de infraestrutura
class InfraPanel(ttk.Frame):
    def __init__(self, parent, callbacks):
        # Inicializa a classe base (Frame) dentro do container "parent"
        super().__init__(parent)
        # Dicionário de callbacks (funções externas passadas para o painel)
        self.cb = callbacks
        self._after_id = None
        # Monta a interface gráfica
        self.setup_ui()

    def setup_ui(self):
        # Configura a coluna principal para expandir proporcionalmente
        self.columnconfigure(0, weight=1)
        # A linha 2 (treeview) será a que expande verticalmente
        self.rowconfigure(2, weight=1)

        # --- Toolbar (linha 0) ---
        f_tools = ttk.Frame(self)
        f_tools.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        # Configura colunas da toolbar para distribuir os botões
        f_tools.columnconfigure(0, weight=0)  # botões à esquerda
        f_tools.columnconfigure(1, weight=0)  # separador
        f_tools.columnconfigure(2, weight=0)
        f_tools.columnconfigure(3, weight=0)
        f_tools.columnconfigure(4, weight=0)
        f_tools.columnconfigure(5, weight=1)  # espaço flexível
        f_tools.columnconfigure(6, weight=0)  # botão à direita

        # Botões à esquerda
        btn_txt = ttk.Button(f_tools, text="📂 Lista TXT", command=self.cb['load_ips'])
        btn_txt.grid(row=0, column=0, padx=2, sticky="w")

        btn_csv = ttk.Button(f_tools, text="📥 Importar CSV (BD)", command=self.cb['import_csv'])
        btn_csv.grid(row=0, column=1, padx=2, sticky="w")

        sep = ttk.Separator(f_tools, orient="vertical")
        sep.grid(row=0, column=2, padx=5, sticky="ns")

        btn_db = ttk.Button(f_tools, text="🗄️ Carregar DB", command=self.cb['load_db'])
        btn_db.grid(row=0, column=3, padx=2, sticky="w")

        btn_add = ttk.Button(f_tools, text="➕ Novo Servidor", command=self.cb['add_server'])
        btn_add.grid(row=0, column=4, padx=2, sticky="w")

        # Espaço flexível para empurrar o botão de deploy para a direita
        espaco = ttk.Frame(f_tools)
        espaco.grid(row=0, column=5, sticky="ew")

        btn_deploy = ttk.Button(f_tools, text="🛠️ Migrar Agente", command=self.cb['deploy'])
        btn_deploy.grid(row=0, column=6, padx=2, sticky="e")

        # --- Barra de busca (linha 1) ---
        f_search = ttk.Frame(self)
        f_search.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5))
        f_search.columnconfigure(1, weight=1)  # campo de entrada expande

        ttk.Label(f_search, text="🔍 Buscar:").grid(row=0, column=0, padx=(0,5))
        self.entry_busca = ttk.Entry(f_search)
        self.entry_busca.grid(row=0, column=1, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", self.filtrar_servidores)

        # --- Treeview (linha 2) ---
        cols = ("IP", "Hostname", "IP Pub", "Funcao", "Cliente", "Status", "Info")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="extended")
        
        # Cabeçalhos
        self.tree.heading("IP", text="IP")
        self.tree.heading("Hostname", text="Hostname")
        self.tree.heading("IP Pub", text="IP Público")
        self.tree.heading("Funcao", text="Função")
        self.tree.heading("Cliente", text="Cliente")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Info", text="Info")
        
        # Configuração de largura e alinhamento
        self.tree.column("IP", width=110, anchor="center")
        self.tree.column("Hostname", width=120, anchor="center")
        self.tree.column("IP Pub", width=110, anchor="center")
        self.tree.column("Funcao", width=80, anchor="center")
        self.tree.column("Cliente", width=200, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Info", width=150, anchor="center")

        # Scrollbar vertical
        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        # Posiciona treeview e scrollbar na linha 2
        self.tree.grid(row=2, column=0, sticky="nsew", padx=5)
        scrolly.grid(row=2, column=1, sticky="ns")

        # Tags para estilizar linhas da tabela
        self.tree.tag_configure("ONLINE", background="#dff9fb")
        self.tree.tag_configure("OFFLINE", background="#ffcccc")
        self.tree.tag_configure("SUCESSO", background="#b8e994")
        self.tree.tag_configure("CRITICO", background="#e74c3c", foreground="white")
        self.tree.tag_configure("DEDICADO", background="#fff0b3")
        self.tree.tag_configure("CREDENCIAL_PROPRIA", background="#d1f2eb")

        # Menu de contexto (clique direito)
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="🖥️ Acessar RDP", command=self.call_rdp)
        self.menu.add_command(label="📋 Copiar IP", command=self.copy_ip)
        self.menu.add_separator()
        self.menu.add_command(label="✏️ Editar Servidor", command=self.call_edit)
        self.menu.add_command(label="🗑️ Excluir Servidor", command=self.call_delete)

        self.tree.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def call_rdp(self):
        sel = self.tree.selection()
        if sel:
            self.cb['rdp'](self.tree.item(sel[0])['values'][0])

    def copy_ip(self):
        sel = self.tree.selection()
        if sel:
            ip = self.tree.item(sel[0])['values'][0]
            self.clipboard_clear()
            self.clipboard_append(ip)
    
    def call_edit(self):
        sel = self.tree.selection()
        if sel:
            ip = self.tree.item(sel[0])['values'][0]
            self.cb['edit_server'](ip)

    def call_delete(self):
        sel = self.tree.selection()
        if sel:
            ip = self.tree.item(sel[0])['values'][0]
            self.cb['delete_server'](ip)

    def filtrar_servidores(self, event=None):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self._aplicar_filtro)
    
    def _aplicar_filtro(self):
        termo = self.entry_busca.get().strip().lower()
        for item in self.tree.get_children():
            valores = self.tree.item(item, 'values')
            texto_item = " ".join(str(v) for v in valores).lower()
            if termo in texto_item:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)
        self._after_id = None