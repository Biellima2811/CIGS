import tkinter as tk
from tkinter import ttk, messagebox

class AddServerDialog(tk.Toplevel):
    def __init__(self, parent, callback_salvar, servidor_atual=None):
        super().__init__(parent)
        self.servidor_atual = servidor_atual # Guarda os dados se for edição
        # Muda o título dinamicamente
        titulo = "Editar Servidor" if servidor_atual else "Registrar Novo Servidor"
        self.title(titulo)

        self.geometry("420x400")
        self.resizable(False, False)  # trava tamanho para não deformar
        self.callback = callback_salvar
        self.setup_ui()

        if self.servidor_atual:
            self.preencher_dados()

    def setup_ui(self):
        # Frame principal de cadastro
        frame = ttk.LabelFrame(self, text='Cadastro de Servidores')
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configuração de colunas para expandir
        frame.columnconfigure(1, weight=1)

        # Linha 0: IP
        ttk.Label(frame, text='Endereço de IP (Local/Externo):').grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_ip = ttk.Entry(frame)
        self.ent_ip.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Linha 1: Hostname
        ttk.Label(frame, text='Hostname (Nome da máquina):').grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ent_host = ttk.Entry(frame)
        self.ent_host.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Linha 2: IP Público
        ttk.Label(frame, text='IP Público (WAN):').grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.ent_pub = ttk.Entry(frame)
        self.ent_pub.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Linha 3: Função
        ttk.Label(frame, text='Função (App, BD, Web...):').grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.cb_func = ttk.Combobox(frame, values=["App", "Banco", "Web", "API", "Backup"], state="readonly")
        self.cb_func.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Linha 4: Cliente/Projeto
        ttk.Label(frame, text='Cliente / Projeto:').grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.ent_cli = ttk.Entry(frame)
        self.ent_cli.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

            # Linha 5: Usuário específico (opcional)
        ttk.Label(frame, text='Usuário específico (opcional):').grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.ent_usuario = ttk.Entry(frame)
        self.ent_usuario.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Linha 6: Senha específica (opcional)
        ttk.Label(frame, text='Senha específica (opcional):').grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.ent_senha = ttk.Entry(frame, show="*")
        self.ent_senha.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        # Botão de salvar (fora do frame, alinhado embaixo)
        ttk.Button(self, text="💾 SALVAR DADOS", command=self.salvar).grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    def salvar(self):
        dados = {
            'ip': self.ent_ip.get().strip(),
            'host': self.ent_host.get().strip(),
            'pub': self.ent_pub.get().strip(),
            'func': self.cb_func.get().strip(),
            'cli': self.ent_cli.get().strip(),
            'usuario' : self.ent_usuario.get().strip() or None,
            'senha' : self.ent_senha.get().strip() or None
        }
        
        if not dados['ip']:
            messagebox.showwarning("Atenção", "O IP é obrigatório!")
            return
        
        # Chama a função do pai para salvar no banco
        self.callback(dados)
        self.destroy()

    def preencher_dados(self):
        """Preenche os campos com os dados existentes do servidor"""
        self.ent_ip.insert(0, self.servidor_atual.get('ip', ''))
        self.ent_host.insert(0, self.servidor_atual.get('hostname', ''))
        self.ent_pub.insert(0, self.servidor_atual.get('ip_publico', ''))
        self.cb_func.set(self.servidor_atual.get('funcao', ''))
        self.ent_cli.insert(0, self.servidor_atual.get('cliente', ''))
        
        # Preenche as credenciais customizadas se existirem
        if self.servidor_atual.get('usuario_especifico'):
            self.ent_usuario.insert(0, self.servidor_atual['usuario_especifico'])
        if self.servidor_atual.get('senha_especifica'):
            self.ent_senha.insert(0, self.servidor_atual['senha_especifica'])