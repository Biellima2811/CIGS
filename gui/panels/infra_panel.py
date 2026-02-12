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
        # Monta a interface gráfica
        self.setup_ui()

    def setup_ui(self):
        # Configura a coluna principal para expandir proporcionalmente
        self.columnconfigure(0, weight=1)
        # Configura a linha 1 (tabela) para expandir
        self.rowconfigure(1, weight=1)

        # Toolbar (barra de ferramentas superior)
        f_tools = ttk.Frame(self)
        f_tools.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        # Botão para carregar lista de IPs a partir de arquivo TXT
        ttk.Button(f_tools, text="📂 Lista TXT", command=self.cb['load_ips']).pack(side="left", padx=2)
        # Botão para carregar lista de servidores dedicados a partir de CSV
        ttk.Button(f_tools, text="📥 Importar CSV (BD)", command=self.cb['import_csv']).pack(side="left", padx=2)

        ttk.Separator(f_tools, orient="vertical").pack(side="left", padx=5, fill="y")
        ttk.Button(f_tools, text="🗄️ Carregar DB", command=self.cb['load_db']).pack(side="left", padx=2)
        ttk.Button(f_tools, text="➕ Novo Servidor", command=self.cb['add_server']).pack(side="left", padx=2)

        # Botão para migrar agente (ação personalizada)
        ttk.Button(f_tools, text="🛠️ Migrar Agente", command=self.cb['deploy']).pack(side="right", padx=2)

        # Tabela (Treeview) para listar servidores
        # Selectmode=extended permite múltiplas seleções (Ctrl+Click)
        cols = ("IP", "Hostname", "IP Pub", "Funcao", "Cliente", "Status", "Info")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="extended")
        
        # Cabeçalhos das colunas
        self.tree.heading("IP", text="IP")
        self.tree.heading("Hostname", text="Hostname")
        self.tree.heading("IP Pub", text="IP Público")
        self.tree.heading("Funcao", text="Função")
        self.tree.heading("Cliente", text="Cliente")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Info", text="Info")
        
        # Configuração de largura e alinhamento das colunas
        self.tree.column("IP", width=110, anchor="center")
        self.tree.column("Hostname", width=120, anchor="center")
        self.tree.column("IP Pub", width=110, anchor="center")
        self.tree.column("Funcao", width=80, anchor="center")
        self.tree.column("Cliente", width=200, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Info", width=150, anchor="center")

        # Scrollbar vertical para a tabela
        scrolly = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        # Posiciona a tabela e a barra de rolagem
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5)
        scrolly.grid(row=1, column=1, sticky="ns")

        # Tags para estilizar linhas da tabela conforme status
        self.tree.tag_configure("ONLINE", background="#dff9fb")   # Azul claro
        self.tree.tag_configure("OFFLINE", background="#ffcccc")  # Vermelho claro
        self.tree.tag_configure("SUCESSO", background="#b8e994")  # Verde claro
        self.tree.tag_configure("CRITICO", background="#e74c3c", foreground="white") # Vermelho forte
        self.tree.tag_configure("DEDICADO", background="#fff0b3") # Amarelo claro

        # Menu de contexto (clique direito)
        self.menu = Menu(self, tearoff=0)
        # Opção para acessar RDP
        self.menu.add_command(label="🖥️ Acessar RDP", command=self.call_rdp)
        # Opção para copiar IP
        self.menu.add_command(label="📋 Copiar IP", command=self.copy_ip)
        # Associa o clique direito à função show_menu
        self.tree.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        # Identifica a linha clicada com botão direito
        item = self.tree.identify_row(event.y)
        if item:
            # Se clicou em algo fora da seleção atual, seleciona apenas esse item
            # Se clicou dentro de um grupo já selecionado, mantém o grupo (útil para ações em lote futuras)
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            # Exibe o menu de contexto na posição do clique
            self.menu.post(event.x_root, event.y_root)

    def call_rdp(self):
        # Abre RDP apenas para o primeiro item da seleção
        sel = self.tree.selection()
        if sel:
            # Pega o IP da primeira linha selecionada e chama o callback 'rdp'
            self.cb['rdp'](self.tree.item(sel[0])['values'][0])

    def copy_ip(self):
        # Copia o IP da primeira linha selecionada para a área de transferência
        sel = self.tree.selection()
        if sel:
            ip = self.tree.item(sel[0])['values'][0]
            self.clipboard_clear()
            self.clipboard_append(ip)
