"""
CIGS - Central de Comandos Integrados v3.4 (Full Fix)
Aplicação desktop para gerenciamento e automação de infraestrutura de servidores
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, Toplevel, Label, Entry, Button
from ttkthemes import ThemedTk
import threading
import subprocess
import os
import csv
import webbrowser
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse
import random, hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tkinter.simpledialog as simpledialog
import sqlite3

# Imports do Núcleo
from core.network_ops import CIGSCore
from core.sheets_manager import CIGSSheets
from core.security_manager import CIGSSecurity
from core.db_manager import CIGSDatabase
from gui.dialogs.schedule_dialog import ScheduleDialog
from core.email_manager import CIGSEmailManager

# Imports dos Painéis
from gui.panels.top_panel import TopPanel
from gui.panels.infra_panel import InfraPanel
from gui.panels.db_panel import DbPanel
from gui.panels.dashboard_panel import DashboardPanel
from gui.dialogs.add_server_dialog import AddServerDialog
from gui.panels.war_generator import WarGeneratorPanel

class CIGSApp:
    """
    Classe principal da aplicação CIGS
    """
    
    def __init__(self, root, usuario="Operador", nivel="tecnico"):
        self.root = root
        # Recebemos as credenciais vindas do login do PostgreSQL
        self.usuario_logado = usuario
        self.nivel_acesso = nivel
        self.auth_ok = True

        self.db = CIGSDatabase() 
        self.core = CIGSCore()
        self.sheets = CIGSSheets()
        self.security = CIGSSecurity()
        self.email_manager = CIGSEmailManager(self.security)
                
        self.monitor_active = False 
        self.setup_window()
        self.setup_sidebar_layout() 
        self.setup_menu()
        
        self.monitor_active = True
        self.monitor_thread()
        self.root.after(500, self.carregar_servidores_db)

    def _criar_senha_mestra(self):
        """Janela para definir a senha mestra na primeira execução."""
        win = tk.Toplevel(self.root)
        win.title("Configuração Inicial - CIGS")
        win.geometry("400x250")
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="Defina a senha mestra do sistema", font=("Arial", 12, "bold")).pack(pady=20)

        tk.Label(win, text="Nova senha:").pack()
        entry_senha1 = tk.Entry(win, show="*", width=30)
        entry_senha1.pack(pady=5)

        tk.Label(win, text="Confirme a senha:").pack()
        entry_senha2 = tk.Entry(win, show="*", width=30)
        entry_senha2.pack(pady=5)

        def confirmar():
            senha1 = entry_senha1.get()
            senha2 = entry_senha2.get()
            if not senha1:
                messagebox.showerror("Erro", "A senha não pode estar vazia.")
                return
            if senha1 != senha2:
                messagebox.showerror("Erro", "As senhas não coincidem.")
                return
            self.security.definir_senha_mestra(senha1)
            self.auth_ok = True
            win.destroy()

        tk.Button(win, text="Confirmar", command=confirmar, bg="#27ae60", fg="white", padx=20, pady=5).pack(pady=20)

        self.root.wait_window(win)

    def _fazer_login(self):
        """Janela de login com senha mestra."""
        win = tk.Toplevel(self.root)
        win.title("Acesso ao CIGS")
        win.geometry("350x200")
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="CIGS - Central de Comandos", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Label(win, text="Senha mestra:").pack()
        entry_senha = tk.Entry(win, show="*", width=30)
        entry_senha.pack(pady=5)
        entry_senha.focus()

        def verificar():
            if self.security.verificar_senha_mestra(entry_senha.get()):
                self.auth_ok = True
                win.destroy()
            else:
                messagebox.showerror("Erro", "Senha incorreta!")
                entry_senha.delete(0, tk.END)

        win.bind('<Return>', lambda e: verificar())
        tk.Button(win, text="Entrar", command=verificar, bg="#2980b9", fg="white", padx=20, pady=5).pack(pady=20)

        self.root.wait_window(win)
    # ==========================================
    # CONFIGURAÇÃO DA INTERFACE
    # ==========================================
    
    def setup_window(self):
        """Configura as propriedades da janela principal"""
        self.root.title("CIGS - Central de Comandos Integrados Versão 3.7.3.2 (Estavel)")
        self.root.geometry("1280x850")
        try: self.root.state('zoomed')
        except: pass
        try: self.root.iconbitmap("assets/CIGS.ico")
        except: pass
        
    def setup_sidebar_layout(self):
        """Configura o layout principal com sidebar e área de conteúdo"""
        self.paned = tk.PanedWindow(self.root, orient="horizontal", sashwidth=5, bg="#2c3e50")
        self.paned.pack(fill="both", expand=True)

        # --- SIDEBAR ---
        self.frame_sidebar = tk.Frame(self.paned, bg="#2c3e50", width=220)
        self.paned.add(self.frame_sidebar, minsize=200)
        
        tk.Label(self.frame_sidebar, text="C.I.G.S", font=("Impact", 28), fg="#ecf0f1", bg="#2c3e50").pack(pady=(30, 10))
        tk.Label(self.frame_sidebar, text="Comandos Integrados", font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 30))

        btn_style = {"font": ("Segoe UI", 11, "bold"), "bg": "#34495e", "fg": "white", 
                    "activebackground": "#2980b9", "activeforeground": "white", 
                    "bd": 0, "pady": 12, "cursor": "hand2", "anchor": "w", "padx": 20}
        
        self.btn_infra = tk.Button(self.frame_sidebar, text="📡  INFRAESTRUTURA", command=lambda: self.show_page("infra"), **btn_style)
        self.btn_infra.pack(fill="x", pady=2)
        
        self.btn_dash = tk.Button(self.frame_sidebar, text="📊  DASHBOARD", command=lambda: self.show_page("dash"), **btn_style)
        self.btn_dash.pack(fill="x", pady=2)
        
        self.btn_db = tk.Button(self.frame_sidebar, text="🏥  CLÍNICA BD", command=lambda: self.show_page("db"), **btn_style)
        self.btn_db.pack(fill="x", pady=2)

        self.btn_war = tk.Button(self.frame_sidebar, text="📦  GERADOR WAR", command=lambda: self.show_page("war"), **btn_style)
        self.btn_war.pack(fill="x", pady=2)

        # --- CONTEÚDO ---
        self.frame_content = tk.Frame(self.paned, bg="#ecf0f1")
        self.paned.add(self.frame_content, stretch="always")
        self.frame_content.columnconfigure(0, weight=1)
        self.frame_content.rowconfigure(1, weight=1)

        # 1. Painel Superior
        self.top_panel = TopPanel(self.frame_content, self.core.verificar_validade_link)
        self.top_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # 2. Container das Páginas
        self.container = tk.Frame(self.frame_content)
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        # Instancia os painéis
        self.pages = {}
        self.infra_panel = InfraPanel(self.container, {
            'rdp': self.rdp_connect, 
            'deploy': self.btn_deploy_massa,
            'load_ips': self.btn_carregar_padrao, 
            'import_csv': self.btn_importar_csv_bd,
            'load_db': self.carregar_servidores_db,
            'add_server': self.abrir_add_server,
            'edit_server': self.abrir_edit_server,   # NOVO
            'delete_server': self.deletar_servidor   # NOVO
        })
        self.pages["infra"] = self.infra_panel
        
        self.dash_panel = DashboardPanel(self.container, self.db, self.core)
        self.pages["dash"] = self.dash_panel
        
        self.db_panel = DbPanel(self.container, 
                               self.executar_manutencao_bd, 
                               self.iniciar_scan_bancos, 
                               self.iniciar_agendamento)
        self.pages["db"] = self.db_panel

        self.war_panel = WarGeneratorPanel(self.container, self.log_visual, self.update_progress)
        self.pages["war"] = self.war_panel

        if self.nivel_acesso == 'admin':
            self.btn_users = tk.Button(self.frame_sidebar, text="👥  GESTÃO USUÁRIOS", 
                                      command=lambda: self.show_page("users"), **btn_style)
            self.btn_users.pack(fill="x", pady=2)
            
            # Cria o container visual da aba
            self.users_panel = tk.Frame(self.container, bg="#ecf0f1")
            self.pages["users"] = self.users_panel
            self.users_panel.grid(row=0, column=0, sticky="nsew")
            self.montar_aba_usuarios()

        # Posiciona todos os painéis no mesmo grid
        for p in self.pages.values(): 
            p.grid(row=0, column=0, sticky="nsew")
        self.show_page("infra")

        # 3. Rodapé
        self.frame_bot = tk.Frame(self.frame_content)
        self.frame_bot.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.frame_bot.columnconfigure(0, weight=1)
        
        # Área de log
        self.txt_log = scrolledtext.ScrolledText(self.frame_bot, height=6, font=("Consolas", 9))
        self.txt_log.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame_bot, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.lbl_progress = tk.Label(self.frame_bot, text="Aguardando comando...", font=("Arial", 8), fg="gray")
        self.lbl_progress.grid(row=2, column=0, sticky="w")

        # Botões de ação
        f_act = tk.Frame(self.frame_bot)
        f_act.grid(row=3, column=0, sticky="ew")
        f_act.columnconfigure(0, weight=1)
        
        ttk.Label(f_act, text='© 2026 Gabriel Levi · Fortes Tecnologia').grid(row=0, column=0, sticky="w", padx=5)
        
        # Botões alinhados à direita (ordem IMPORTANTE!)
        tk.Button(f_act, text="☢️ DISPARAR EM TODOS", command=self.btn_disparar_todos, 
                 bg="black", fg="#e74c3c", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=5, padx=5)
        tk.Button(f_act, text="🚀 DISPARAR MISSÃO (Checklist)", command=self.pre_flight_checklist, 
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=4, padx=5)
        tk.Button(f_act, text='❌ Abortar Disparo', command=self.btn_abortar, 
                 bg='#6D1B08', fg='white', font=("Arial", 10, "bold"), padx=10).grid(row=0, column=3, padx=5)
        tk.Button(f_act, text="📡 Scanear Infra", command=self.btn_scanear).grid(row=0, column=2, padx=5)
        tk.Button(f_act, text="📊 Ver Relatório", command=self.btn_relatorio_final).grid(row=0, column=1, padx=5)

    def show_page(self, name):
        """Alterna entre as páginas/painéis da aplicação"""
        self.pages[name].tkraise()
        def_bg = "#34495e"
        self.btn_infra.config(bg=def_bg)
        self.btn_dash.config(bg=def_bg)
        self.btn_db.config(bg=def_bg)
        self.btn_war.config(bg=def_bg)
        if name == "infra": self.btn_infra.config(bg="#2980b9")
        if name == "dash": self.btn_dash.config(bg="#2980b9")
        if name == "db": self.btn_db.config(bg="#2980b9")
        if name == "war": self.btn_war.config(bg="#2980b9")
    
    def setup_menu(self):
        """Configura a barra de menus superior da aplicação"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        f = tk.Menu(menubar, tearoff=0)
        f.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=f)
        
        c = tk.Menu(menubar, tearoff=0)
        c.add_command(label="Email", command=self.janela_config_email)
        menubar.add_cascade(label="Config", menu=c)
        
        h = tk.Menu(menubar, tearoff=0)
        h.add_command(label="Sobre", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=h)

    # ==========================================
    # MÉTODOS AUXILIARES (UI)
    # ==========================================
    
    def log_visual(self, msg):
        """Adiciona mensagem à área de log visual"""
        self.root.after(0, lambda: self.txt_log.insert(tk.END, 
                     f"{datetime.now().strftime('%H:%M:%S')} {msg}\n") or self.txt_log.see(tk.END))

    def update_progress(self, current, total, message=""):
        """Atualiza a barra de progresso"""
        percent = (current / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self._ui_update_prog(percent, f"{current}/{total} - {message}"))

    def _ui_update_prog(self, val, txt):
        """Atualização thread-safe da UI"""
        self.progress_var.set(val)
        self.lbl_progress.config(text=txt)

    def _atualizar_tree_seguro(self, item_id, valores, tags):
        """Atualiza a árvore apenas se o item ainda existir"""
        try:
            if self.infra_panel.tree.exists(item_id):
                self.infra_panel.tree.item(item_id, values=valores, tags=tags)
        except:
            pass

    # ==========================================
    # GERENCIAMENTO DE SERVIDORES
    # ==========================================
    
    def abrir_add_server(self):
        AddServerDialog(self.root, self.salvar_novo_servidor)
    
    def salvar_novo_servidor(self, dados):
        """Salva no SQLite e atualiza a tela"""
        suc, msg = self.db.adicionar_servidor(dados['ip'], 
                                              dados['host'], 
                                              dados['pub'], 
                                              dados['func'], 
                                              dados['cli'],
                                              dados.get('usuario'), 
                                              dados.get('senha'))
        if suc:
            messagebox.showinfo("Sucesso", msg)
            self.carregar_servidores_db()
        else:
            messagebox.showerror("Erro BD", msg)

    def carregar_servidores_db(self):
        """Lê do SQLite e preenche a tabela"""
        try:
            servidores = self.db.listar_servidores()
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            
            for s in servidores:
                tags = ("DEDICADO",)
                if s.get('usuario_especifico'):
                    tags = ("DEDICADO", "CREDENCIAL_PROPRIA")
                self.infra_panel.tree.insert("", "end", values=(
                    s['ip'], s['hostname'], s['ip_publico'], s['funcao'], s['cliente'], "...", "-"
                ), tags=tags)
            
            self.log_visual(f"Base de Dados: {len(servidores)} ativos carregados.")
            self.dash_panel.update_plots()
        except Exception as e:
            self.log_visual(f"Erro ao carregar DB: {e}")
            
    def obter_credenciais_servidor(self, ip):
        """Retorna (usuario, senha) específicos do servidor ou (None, None)."""
        try:
            conn = self.db.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT usuario_especifico, senha_especifica FROM servidores WHERE ip = ?", 
                (ip,)
            )
            row = cursor.fetchone()
            conn.close()
            if row and row['usuario_especifico']:
                return row['usuario_especifico'], row['senha_especifica']
        except Exception:
            pass
        return None, None
    
    def deletar_servidor(self, ip):
        """Confirma e remove o servidor do banco de dados"""
        # Verificação de Patente
        if getattr(self, 'nivel_acesso', 'tecnico') != 'admin':
            messagebox.showerror("Acesso Negado", "Negativo, Operador! Apenas o Comandante (Admin) pode excluir servidores do banco.")
            return
        
        resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja remover o servidor {ip}?")
        if resposta:
            self.db.remover_servidor(ip)
            self.log_visual(f"🗑️ Servidor {ip} removido do banco.")
            self.carregar_servidores_db() # Atualiza a tabela na tela

    def abrir_edit_server(self, ip):
        """Busca os dados do IP e abre a tela em modo edição"""
        servidor_dados = self.db.buscar_servidor_por_ip(ip)
        
        if servidor_dados:
            # Passamos os dados atuais para a tela
            AddServerDialog(self.root, lambda novos_dados: self.salvar_edicao_servidor(ip, novos_dados), servidor_dados)
        else:
            messagebox.showerror("Erro", "Servidor não encontrado no banco de dados!")

    def salvar_edicao_servidor(self, ip_antigo, dados):
        """Salva as alterações do servidor no banco e atualiza a tela"""
        suc, msg = self.db.atualizar_servidor(
            ip_antigo,
            dados['ip'], 
            dados['host'], 
            dados['pub'], 
            dados['func'], 
            dados['cli'],
            dados.get('usuario'), 
            dados.get('senha')
        )
        if suc:
            self.log_visual(f"✏️ Servidor {ip_antigo} atualizado com sucesso.")
            self.carregar_servidores_db()
        else:
            messagebox.showerror("Erro BD", msg)

    def btn_carregar_padrao(self):
        """Carrega lista de IPs a partir de arquivo TXT"""
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if path:
            ips = self.core.carregar_lista_ips(path)
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            for ip in ips: 
                self.infra_panel.tree.insert("", "end", values=(ip, "...", "-", "-", "-", "-", "-"))
            self.log_visual(f"Carregados: {len(ips)}")

    def btn_importar_csv_bd(self):
        """
        Função Dupla:
        - Gera template se o usuário pedir.
        - Importa CSV para o Banco de Dados se o arquivo for selecionado.
        """
        # Pergunta tática ao usuário
        escolha = messagebox.askyesnocancel(
            "Importação em Massa", 
            "O que deseja fazer?\n\n"
            "SIM: Importar um arquivo CSV existente para o Banco.\n"
            "NÃO: Gerar um modelo (Template) para preencher.\n"
            "CANCELAR: Sair."
        )
        
        if escolha is None: return

        # --- OPÇÃO 1: GERAR TEMPLATE (Clicou em NÃO) ---
        if escolha is False:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", 
                filetypes=[("CSV", "*.csv")], 
                initialfile="template_servidores.csv",
                title="Salvar Modelo de Importação"
            )
            if path:
                try:
                    with open(path, 'w', newline='', encoding='utf-8') as f:
                        f.write("IP;Hostname;IP_Publico;Funcao;Cliente;UsuarioEspecifico;SenhaEspecifica\n")
                        f.write("192.168.1.50;SRV-APP01;200.1.1.50;APP;Cliente Exemplo;;\n")
                        f.write("192.168.1.51;SRV-BD01;200.1.1.51;BD;Cliente Exemplo;fortes\\admin;senha123\n")
                    messagebox.showinfo("Sucesso", f"Template gerado em:\n{path}")
                    try: os.startfile(path)
                    except: pass
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao criar template: {e}")
            return

        # --- OPÇÃO 2: IMPORTAR ARQUIVO (Clicou em SIM) ---
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")], title="Selecione o CSV para Importar")
        if not path: return
        
        try:
            sucessos = 0
            erros = 0
            
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                if not {'IP', 'Hostname'}.issubset(reader.fieldnames):
                    messagebox.showerror("Erro Formato", "O CSV deve ter colunas separadas por PONTO E VÍRGULA (;)\nColunas exigidas: IP;Hostname;IP_Publico;Funcao;Cliente")
                    return

                for row in reader:
                    ip = row.get('IP', '').strip()
                    if not ip: continue
                    
                    suc, msg = self.db.adicionar_servidor(
                        ip, 
                        row.get('Hostname', '-'), 
                        row.get('IP_Publico', '-'), 
                        row.get('Funcao', 'SRV'), 
                        row.get('Cliente', 'Generico'),
                        row.get('UsuarioEspecifico', '').strip() or None,
                        row.get('SenhaEspecifica', '').strip() or None
                    )
                    
                    if suc: sucessos += 1
                    else: 
                        erros += 1
                        self.log_visual(f"Falha ao importar {ip}: {msg}")
            
            self.carregar_servidores_db()
            
            resumo = f"Processamento Finalizado!\n\n✅ Importados: {sucessos}\n❌ Falhas/Duplicados: {erros}"
            if erros > 0: resumo += "\n(Verifique o Log para detalhes)"
            messagebox.showinfo("Relatório de Importação", resumo)
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao ler arquivo: {str(e)}")

    # ==========================================
    # MONITORAMENTO
    # ==========================================
    
    def monitor_thread(self):
        """Inicia thread para monitoramento em tempo real"""
        def run():
            while self.monitor_active:
                try:
                    sel = self.infra_panel.tree.selection()
                    if sel:
                        ip = self.infra_panel.tree.item(sel[0])['values'][0]
                        sis = self.top_panel.get_data()['sistema']
                        res = self.core.checar_status_agente(ip, sis, full=True)
                        if res.get('status') == 'ONLINE':
                            pass
                except: 
                    pass
                time.sleep(3)
        threading.Thread(target=run, daemon=True).start()

    # ==========================================
    # SCAN
    # ==========================================
    
    def btn_scanear(self): 
        """Inicia scan de infraestrutura em thread separada"""
        threading.Thread(target=self.worker_scan).start()

    def worker_scan(self):
        """
        SCAN TÁTICO v4.0
        Varre todos os servidores e coleta status
        """
        sis = self.top_panel.get_data()['sistema']
        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"📡 SCAN INICIADO - Sistema: {sis}")
        self.log_visual(f"{'='*60}\n")
        
        items = self.infra_panel.tree.get_children()
        total = len(items)
        
        if total == 0:
            self.log_visual("⚠️  Lista de servidores vazia!")
            return

        stats = {
            'online': 0,
            'offline': 0,
            'erro': 0,
            'total_clientes': 0,
            'versoes': {},
            'tempo_resposta': []
        }

        for i, item in enumerate(items, 1):
            percent = int((i / total) * 100)
            self.update_progress(i, total, f"Scanning... {percent}% ({i}/{total})")
            
            valores_atuais = list(self.infra_panel.tree.item(item)['values'])
            while len(valores_atuais) < 7:
                valores_atuais.append("-")
            
            ip = valores_atuais[0]
            hostname = valores_atuais[1] if len(valores_atuais) > 1 else "-"
            ip_pub = valores_atuais[2] if len(valores_atuais) > 2 else "-"
            funcao = valores_atuais[3] if len(valores_atuais) > 3 else "-"
            cliente_atual = valores_atuais[4] if len(valores_atuais) > 4 else "-"
            
            self.log_visual(f"[{i}/{total}] 🔍 {ip} ({hostname})...")
            inicio = time.time()
            
            try:
                res = self.core.checar_status_agente(ip, sis, full=False)
                tempo = round((time.time() - inicio) * 1000, 1)
                
                st = res.get('status', 'ERRO')
                msg = res.get('msg', '')
                
                if st == "ONLINE":
                    versao = res.get('version', '?')
                    qtd_clientes = res.get('clientes', 0)
                    ref_cliente = res.get('ref', '-')
                    disk_gb = res.get('disk', '?')
                    ram_perc = res.get('ram', '?')
                    
                    stats['online'] += 1
                    stats['total_clientes'] += qtd_clientes
                    stats['tempo_resposta'].append(tempo)
                    stats['versoes'][versao] = stats['versoes'].get(versao, 0) + 1
                    
                    status_display = f"ON ({qtd_clientes} - {ref_cliente})"
                    tag = "ONLINE"
                    info_extra = f"v{versao} | Disk: {disk_gb}GB | RAM: {ram_perc}%"
                    
                    if str(cliente_atual) in ["-", "", "0", "None", "?", "N/A"] and ref_cliente not in ["-", "", "N/A"]:
                        cliente_atual = ref_cliente
                        self.log_visual(f"   ↳ Cliente atualizado: {cliente_atual}")
                    
                    self.log_visual(f"   ✅ ONLINE | Clientes: {qtd_clientes} | Ref: {ref_cliente} | Versão: {versao} | {tempo}ms")
                else:
                    stats['offline' if st == "OFFLINE" else 'erro'] += 1
                    status_display = st
                    tag = "OFFLINE"
                    info_extra = msg
                    self.log_visual(f"   ❌ {st} | {msg}")
                    
            except Exception as e:
                stats['erro'] += 1
                status_display = "ERRO"
                tag = "OFFLINE"
                info_extra = str(e)[:50]
                self.log_visual(f"   💥 ERRO INESPERADO: {str(e)[:100]}")

            novos_valores = [
                ip, hostname, ip_pub, funcao, cliente_atual, status_display, info_extra
            ]
            
            self.root.after(0, lambda id=item, v=novos_valores, t=tag: 
                          self._atualizar_tree_seguro(id, v, (t,)))
            
            if i % 10 == 0:
                time.sleep(0.1)

        latencia_media = 0
        if stats['tempo_resposta']:
            latencia_media = round(sum(stats['tempo_resposta']) / len(stats['tempo_resposta']), 1)
        
        try:
            self.db.registrar_scan(
                total=total,
                on=stats['online'],
                off=stats['offline'] + stats['erro'],
                latencia=latencia_media
            )
        except Exception as e:
            self.log_visual(f"⚠️  Erro ao registrar histórico: {e}")
        
        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"📊 RESUMO DO SCAN - {sis}")
        self.log_visual(f"{'='*60}")
        self.log_visual(f"✅ Online:  {stats['online']}")
        self.log_visual(f"❌ Offline: {stats['offline']}")
        self.log_visual(f"⚠️  Erros:   {stats['erro']}")
        self.log_visual(f"📋 Total:    {total}")
        self.log_visual(f"\n👥 Total de clientes ativos: {stats['total_clientes']}")
        self.log_visual(f"⏱️  Latência média: {latencia_media}ms")
        
        if stats['versoes']:
            self.log_visual(f"\n📦 Versões do Agente:")
            for versao, qtd in sorted(stats['versoes'].items()):
                percent = round((qtd / stats['online']) * 100, 1) if stats['online'] > 0 else 0
                self.log_visual(f"   • {versao}: {qtd} servidores ({percent}%)")
        
        if total > 0:
            sucesso_percent = round((stats['online'] / total) * 100, 1)
            self.log_visual(f"\n🎯 Disponibilidade: {sucesso_percent}%")
        
        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"🏁 SCAN FINALIZADO")
        self.log_visual(f"{'='* 60}\n")
        
        self.update_progress(total, total, f"Scan Completo: {stats['online']} ON / {stats['offline']} OFF / {stats['erro']} ERRO")
        self.root.after(0, self.dash_panel.update_plots)

    # ==========================================
    # DEPLOY
    # ==========================================
    
    def btn_deploy_massa(self):
        """Inicia deploy em massa do agente CIGS"""
        if not messagebox.askyesno("ATENÇÃO", "Deploy do Agente para TODOS?"): 
            return
        threading.Thread(target=self.worker_deploy).start()

    def worker_deploy(self):
        """DEPLOY TÁTICO v6.0"""
        if os.path.exists("CIGS_Agent.exe"):
            origem = "CIGS_Agent.exe"
            modo = "ARQUIVO"
        elif os.path.exists("dist/CIGS_Agent.exe"):
            origem = "dist/CIGS_Agent.exe"
            modo = "ARQUIVO"
        elif os.path.exists("CIGS_Agent.dist"):
            origem = "CIGS_Agent.dist"
            modo = "PASTA"
        else:
            self.log_visual("❌ ERRO: CIGS_Agent.exe não encontrado")
            return

        if not os.path.exists("nssm.exe") or not os.path.exists("Instalar_CIGS.bat"):
            self.log_visual("❌ ERRO: Faltando nssm.exe ou Instalar_CIGS.bat")
            return

        dados_painel = self.top_panel.get_data()
        user = dados_painel['user'].strip()
        password = dados_painel['pass'].strip()
        
        if not user or not password:
            self.log_visual("❌ ERRO: Usuário e senha obrigatórios")
            return

        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"🚀 DEPLOY TÁTICO INICIADO - MODO: {modo}")
        self.log_visual(f"{'='*60}\n")

        items = self.infra_panel.tree.get_children()
        total = len(items)
        
        if total == 0:
            self.log_visual("❌ Nenhum servidor na lista!")
            return

        stats = {'sucesso': 0, 'falha': 0, 'pulado': 0}

        for i, item in enumerate(items, 1):
            ip = self.infra_panel.tree.item(item)['values'][0]
            self.update_progress(i, total, f"Processando {ip}...")
            
            if "OFFLINE" in self.infra_panel.tree.item(item).get('tags', []):
                self.log_visual(f"⏭️  {ip}: Servidor offline - pulando")
                stats['pulado'] += 1
                continue

            dest_dir = f"\\\\{ip}\\C$\\CIGS"
            user_esp, pass_esp = self.obter_credenciais_servidor(ip)
            dados_painel = self.top_panel.get_data()
            user = user_esp if user_esp else dados_painel['user'].strip()
            password = pass_esp if pass_esp else dados_painel['pass'].strip()

            try:
                self.log_visual(f"🔑 {ip}: Autenticando...")
                subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
                cmd_auth = f'net use \\\\{ip}\\C$ /user:"{user}" "{password}"'
                if subprocess.run(cmd_auth, shell=True, capture_output=True).returncode != 0:
                    raise Exception("Falha na autenticação")

                self.log_visual(f"🛑 {ip}: Neutralizando processos...")
                subprocess.run(f'sc \\\\{ip} stop CIGS_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /U "{user}" /P "{password}" /IM CIGS_Agent.exe /F', 
                            shell=True, stdout=subprocess.DEVNULL)
                time.sleep(2)

                self.log_visual(f"📋 {ip}: Copiando arquivos...")
                subprocess.run(f'mkdir "{dest_dir}" 2>nul', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'copy /Y "nssm.exe" "{dest_dir}\\nssm.exe"', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'copy /Y "Instalar_CIGS.bat" "{dest_dir}\\Instalar_CIGS.bat"', shell=True, stdout=subprocess.DEVNULL)
                
                if modo == "PASTA":
                    cmd_copy = f'xcopy "{origem}" "{dest_dir}" /E /I /Y /Q'
                else:
                    cmd_copy = f'copy /Y "{origem}" "{dest_dir}\\CIGS_Agent.exe"'
                
                if subprocess.run(cmd_copy, shell=True).returncode != 0:
                    raise Exception("Falha na cópia do agente")

                self.log_visual(f"⚙️  {ip}: Configurando serviço...")
                cmd_wmic = f'wmic /node:"{ip}" /user:"{user}" /password:"{password}" process call create "cmd.exe /c C:\\CIGS\\Instalar_CIGS.bat"'
                
                if subprocess.run(cmd_wmic, shell=True, capture_output=True).returncode == 0:
                    self.log_visual(f"✅ {ip}: SUCESSO")
                    stats['sucesso'] += 1
                else:
                    raise Exception("Falha na instalação")
                    
            except Exception as e:
                self.log_visual(f"❌ {ip}: ERRO - {str(e)}")
                stats['falha'] += 1
                # ENVIA ALERTA DE ERRO CRÍTICO
                self.email_manager.enviar_email_alerta(
                    sistema=dados_painel['sistema'],
                    servidor=ip,
                    erro=str(e),
                    criticidade="ALTA"
                )
            
            finally:
                subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)

        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"📊 RELATÓRIO FINAL DO DEPLOY")
        self.log_visual(f"{'='*60}")
        self.log_visual(f"✅ Sucesso: {stats['sucesso']}")
        self.log_visual(f"❌ Falha:   {stats['falha']}")
        self.log_visual(f"⏭️  Pulado:  {stats['pulado']}")
        self.log_visual(f"{'='*60}\n")
        
        self.update_progress(total, total, "Deploy Finalizado")

    # ==========================================
    # DISPARO DE MISSÃO (CHECKLIST COMPLETO)
    # ==========================================
    
    def btn_disparar_todos(self):
        """Seleciona automaticamente TODOS os servidores e inicia o checklist"""
        todos_itens = self.infra_panel.tree.get_children()
        if not todos_itens:
            messagebox.showwarning("Aviso", "A lista está vazia! Carregue os servidores primeiro.")
            return
            
        if not messagebox.askyesno("CONFIRMAÇÃO DE COMBATE", 
                                  f"ATENÇÃO: Você vai disparar contra {len(todos_itens)} servidores.\n\nDeseja realmente prosseguir?"):
            return

        self.infra_panel.tree.selection_set(todos_itens)
        self.pre_flight_checklist()

    def pre_flight_checklist(self):
        """
        Executa checklist pré-disparo para validar condições
        Abre janela modal com validações passo a passo
        """
        sel = self.infra_panel.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhum servidor selecionado.\nSelecione na lista.")
            return
        
        win = Toplevel(self.root)
        win.title("Checklist")
        win.geometry("450x500")
        tk.Label(win, text="Validação Pré-Missão", font=("Arial", 14, "bold")).pack(pady=10)
        
        lst = tk.Listbox(win, font=("Consolas", 10), bg="#fdfefe")
        lst.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_go = tk.Button(win, text="AUTORIZAR DISPARO", state="disabled", 
                          bg="#e74c3c", fg="white",
                          command=lambda: [win.destroy(), 
                                         threading.Thread(target=self.worker_disparo, args=(sel,)).start()])
        btn_go.pack(pady=15)

        def add(msg, color="black"):
            lst.insert(tk.END, msg)
            lst.itemconfig(tk.END, fg=color)
            lst.see(tk.END)
            win.update()
            time.sleep(0.2)

        def run_check():
            erros = 0
            d = self.top_panel.get_data()
            add(f"1. Alvos: {len(sel)}", "blue")
            
            if not d['url'] and "Rede Local" not in d['tipo']:
                add("❌ Link AWS vazio!", "red")
                erros += 1
            else:
                add("✅ Parâmetros OK", "green")
            
            if "Rede Local" in d['tipo']:
                paths = [
                    os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                    os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")
                ]
                if any(os.path.exists(p) for p in paths):
                    add("✅ Arquivo local OK", "green")
                else:
                    add("❌ Arquivo local 404!", "red")
                    erros += 1
            
            ip_teste = self.infra_panel.tree.item(sel[0])['values'][0]
            res = self.core.checar_status_agente(ip_teste, d['sistema'])
            if res.get('status') == "ONLINE":
                add("✅ Conectividade OK", "green")
            else:
                add("⚠️ Agente Offline/Instável", "orange")

            if erros == 0:
                add("\n>>> PRONTO PARA COMBATE <<<", "green")
                btn_go.config(state="normal", bg="#27ae60")
            else:
                add("\n❌ ABORTAR", "red")

        threading.Thread(target=run_check).start()

    def worker_disparo(self, selecionados):
        """
        Worker que executa disparo de atualizações para servidores selecionados
        """
        d = self.top_panel.get_data()
        self.log_visual(f">>> DISPARO (Script: {d['script']} | Args: {d['params']}) <<<")
        
        local_exe = ""
        if "Rede Local" in d['tipo']:
            paths = [
                os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")
            ]
            local_exe = next((p for p in paths if os.path.exists(p)), None)
            modo = "APENAS_EXEC"
        else: 
            modo = "COMPLETO"

        try:
            db = datetime.strptime(f"{d['data']} {d['hora']}", "%d/%m/%Y %H:%M")
        except:
            self.log_visual("❌ ERRO: Formato de data/hora inválido!")
            return

        self.log_visual(">>> PROCESSANDO DISPARO <<<")
        cnt = 0
        
        for item_id in selecionados:
            item = self.infra_panel.tree.item(item_id)
            ip = item['values'][0]
            user_esp, pass_esp = self.obter_credenciais_servidor(ip)
            user_atual = user_esp if user_esp else d['user']
            pass_atual = pass_esp if pass_esp else d['pass']

            
            if cnt > 0 and cnt % 10 == 0:
                db += timedelta(minutes=15)
            dt_str = db.strftime("%d/%m/%Y %H:%M")
            
            copia_ok = True
            msg = ""
            
            if modo == "APENAS_EXEC":
                pasta_sis = "Ponto" if d['sistema'] == "PONTO" else d['sistema']
                dest = f"\\\\{ip}\\C$\\Atualiza\\CloudUp\\CloudUpCmd\\{d['sistema']}\\Atualizadores\\{pasta_sis}\\{d['sistema']}.exe"
                
                self.log_visual(f"-> {ip}: Copiando...")
                try:
                    path_dir = os.path.dirname(dest)
                    subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                    subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, 
                                 stdout=subprocess.DEVNULL, check=True)
                except:
                    try:
                        self.log_visual(f"-> {ip}: Autenticando...")
                        subprocess.run(f'net use \\\\{ip}\\C$ /user:{user_atual} {pass_atual}', 
                                     shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, 
                                     stdout=subprocess.DEVNULL, check=True)
                        subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
                    except:
                        copia_ok = False
                        msg = "Erro Copy"

            if copia_ok:
                try:
                    nome = os.path.basename(urlparse(d['url']).path) or "up.rar"
                except:
                    nome = "up.rar"
                
                suc, msg = self.core.enviar_ordem_agendamento(
                    ip, 
                    d['url'], 
                    nome, dt_str, 
                    user_atual, 
                    pass_atual, 
                    d['sistema'], 
                    modo,
                    script=d['script'], params=d['params']
                )
            else:
                suc = False
            
            # Atualiza interface com resultado
            tag = "SUCESSO" if suc else "OFFLINE"
            self.root.after(0, lambda i=item_id, m=msg, t=tag: 
                          self._atualizar_tree_apos_disparo(i, m, t))
            
            cnt += 1
        
        self.log_visual(">>> FIM DISPARO <<<")

    def _atualizar_tree_apos_disparo(self, item_id, mensagem, tag):
        """Atualiza a árvore após disparo"""
        try:
            if self.infra_panel.tree.exists(item_id):
                valores = list(self.infra_panel.tree.item(item_id)['values'])
                if len(valores) >= 7:
                    valores[6] = mensagem  # Coluna Info
                    self.infra_panel.tree.item(item_id, values=valores, tags=(tag,))
        except:
            pass

    # ==========================================
    # RDP
    # ==========================================
    
    def rdp_connect(self, ip):
        """Estabelece conexão RDP com servidor"""
        user_esp, pass_esp = self.obter_credenciais_servidor(ip)
        d = self.top_panel.get_data()
        user = user_esp if user_esp else d['user']
        password = pass_esp if pass_esp else d['pass']

        try:
            subprocess.run(f'cmdkey /generic:TERMSRV/{ip} /user:"{user}" /pass:"{password}"', shell=True)
            subprocess.Popen(f'mstsc /v:{ip} /admin', shell=True)
        except Exception as e:
            messagebox.showerror("Erro RDP", str(e))

    # ==========================================
    # BANCO DE DADOS
    # ==========================================
    
    def executar_manutencao_bd(self, tipo_acao, motor):
        """Inicia manutenção de banco de dados"""
        db_path = self.db_panel.get_db_path()
        if not db_path:
            messagebox.showwarning("Aviso", "Informe o caminho do banco!")
            return
            
        if messagebox.askyesno("Confirmar", f"Executar {tipo_acao} no {motor}?\nAlvo: {db_path}"):
            threading.Thread(target=self.worker_db_manutencao, args=(tipo_acao, motor, db_path)).start()
        
    def worker_db_manutencao(self, acao, motor, db_path):
        self.root.after(0, lambda: self.db_panel.log(f"\n>>> INICIANDO {acao} ({motor}) <<<"))
        
        sel = self.infra_panel.tree.selection()
        items = sel if sel else self.infra_panel.tree.get_children()
        
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            if "OFFLINE" in self.infra_panel.tree.item(item)['tags']:
                continue
                
            self.root.after(0, lambda i=ip: self.db_panel.log(f"-> Processando {i}..."))
            res = self.core.enviar_comando_bd(ip, motor, acao, db_path)
            self.root.after(0, lambda r=res: self.db_panel.log(f"   Status: {r.get('status')}"))
            
        self.root.after(0, lambda: self.db_panel.log(">>> FIM DA OPERAÇÃO <<<"))

    def iniciar_scan_bancos(self):
        """Inicia varredura de bancos de dados"""
        sel = self.infra_panel.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um servidor!")
            return
        
        ip = self.infra_panel.tree.item(sel[0])['values'][0]
        user_esp, pass_esp = self.obter_credenciais_servidor(ip)
        d = self.top_panel.get_data()
        self.db_panel.log(f"Iniciando varredura em {ip}...")
        user_atual = user_esp if user_esp else d['user']
        pass_atual = pass_esp if pass_esp else d['pass']
        threading.Thread(target=self.worker_scan_bancos, args=(ip, user_atual, pass_atual)).start()

    def worker_scan_bancos(self, ip, user, password):
        r"""
        Varre C:\BDS e D:\BDS via compartilhamento administrativo
        Procura estrutura: BDS \ CLIENTE \ SISTEMA \ ARQUIVO.FDB
        """
        encontrados = []
        drives = ['C$', 'D$']
        
        cmd_auth = f'net use \\\\{ip}\\C$ /user:{user} {password}'
        subprocess.run(cmd_auth, shell=True, stdout=subprocess.DEVNULL)

        for drive in drives:
            root_path = f"\\\\{ip}\\{drive}\\BDS"
            if not os.path.exists(root_path):
                continue
                
            try:
                for cliente in os.listdir(root_path):
                    path_cliente = os.path.join(root_path, cliente)
                    if os.path.isdir(path_cliente):
                        for sistema in os.listdir(path_cliente):
                            if sistema.upper() in ["AC", "AG", "PATRIO", "PONTO"]:
                                path_sistema = os.path.join(path_cliente, sistema)
                                if os.path.isdir(path_sistema):
                                    for arq in os.listdir(path_sistema):
                                        if arq.upper().endswith(".FDB"):
                                            caminho_local = f"{drive[0]}:\\BDS\\{cliente}\\{sistema}\\{arq}"
                                            encontrados.append(caminho_local)
            except Exception as e:
                self.root.after(0, lambda e=e: self.db_panel.log(f"Erro scan: {e}"))

        subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
        self.root.after(0, lambda: self.db_panel.atualizar_combo_list(encontrados))

    def iniciar_agendamento(self, motor):
        """Abre diálogo de agendamento"""
        db_path = self.db_panel.get_db_path()
        if not db_path and motor == "FIREBIRD":
            messagebox.showwarning("Aviso", "Selecione o banco de dados primeiro!")
            return
            
        def callback_agendar(data, hora, task_name):
            threading.Thread(target=self.worker_agendar_tarefa, 
                           args=(motor, db_path, data, hora, task_name)).start()
            
        ScheduleDialog(self.root, callback_agendar)

    def worker_agendar_tarefa(self, motor, db_path, data, hora, task_name):
        self.root.after(0, lambda: self.db_panel.log(f"\n>>> AGENDANDO TAREFA: {task_name} <<<"))
        
        sel = self.infra_panel.tree.selection()
        items = sel if sel else self.infra_panel.tree.get_children()
        
        servidores_afetados = []
        total_clientes = 0

        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            if "OFFLINE" in self.infra_panel.tree.item(item)['tags']: 
                continue
            # Tenta obter número de clientes para estatística
            try:
                res = self.core.checar_status_agente(ip, "AC")
                clientes = res.get('clientes', 0)
                total_clientes += clientes
                servidores_afetados.append(ip)
            except:
                pass
            self.root.after(0, lambda i=ip: self.db_panel.log(f"-> {i}: Criando tarefa..."))
        # ENVIA EMAIL DE CONFIRMAÇÃO!
        if servidores_afetados:
            sistema = self.top_panel.get_data()['sistema']
            self.email_manager.enviar_email_agendamento(
                sistema=sistema,
                data=data,
                hora=hora,
                num_servidores=len(servidores_afetados),
                clientes=total_clientes
            )
            self.log_visual(f"📧 Email de confirmação enviado para {sistema}")
            
        self.root.after(0, lambda: self.db_panel.log(">>> AGENDAMENTO CONCLUÍDO <<<"))

    # ==========================================
    # RELATÓRIOS
    # ==========================================
    
    def btn_relatorio_final(self):
        """Solicita confirmação e inicia geração de relatório"""
        if messagebox.askyesno("Relatório", "Gerar?"):
            threading.Thread(target=self.worker_relatorio).start()
    
    def worker_relatorio(self):
        """
        Worker que gera relatório consolidado de execuções
        Agora com estatísticas detalhadas e email completo
        """
        data = self.top_panel.get_data()
        sis = data['sistema']
        
        try:
            dt = datetime.strptime(data['data'], "%d/%m/%Y").strftime("%Y%m%d")
        except:
            dt = datetime.now().strftime("%Y%m%d")
        
        self.log_visual(">>> GERANDO RELATÓRIO <<<")
        
        stats = {
            'total': 0,
            'sucessos': 0,
            'falhas': 0,
            'servidores': []
        }
        
        csv_d = []
        
        items = self.infra_panel.tree.get_children()
        for item in items:
            valores = self.infra_panel.tree.item(item)['values']
            ip = valores[0]
            hostname = valores[1] if len(valores) > 1 else ip
            status = valores[5] if len(valores) > 5 else ""
            cliente = valores[4] if len(valores) > 4 else "-"
            
            servidor_info = {
                'ip': ip,
                'hostname': hostname,
                'status': status,
                'clientes': cliente,
                'resultado': '-'
            }
            
            if "OFFLINE" not in status:
                res = self.core.obter_relatorio_agente(ip, sis, dt)
                if "erro" not in res:
                    t = res.get('total', 0)
                    s = res.get('sucessos', 0)
                    p = res.get('porcentagem', 0)
                    falhas = t - s
                    
                    stats['total'] += t
                    stats['sucessos'] += s
                    stats['falhas'] += falhas
                    
                    servidor_info['resultado'] = f"{s}/{t} ({p}%)"
                    
                    csv_d.append([ip, sis, t, s, f"{p}%", res.get('arquivo', '-')])
                    
                    self.root.after(0, lambda i=item, m=f"Log: {s}/{t}": 
                                self._atualizar_tree_relatorio(i, m))
            
            stats['servidores'].append(servidor_info)
        
        # Salva CSV
        csv_path = None
        if csv_d:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nome = f"Relatorio_{sis}_{timestamp}.csv"
                
                with open(nome, 'w', newline='', encoding='utf-8-sig') as f:
                    w = csv.writer(f, delimiter=';')
                    w.writerow(["IP", "Sistema", "Total", "Sucessos", "%", "Arquivo"])
                    w.writerows(csv_d)
                
                csv_path = os.path.abspath(nome)
                self.log_visual(f"📁 CSV salvo: {nome}")
                
            except Exception as e:
                self.log_visual(f"❌ Erro ao salvar CSV: {e}")
        
        # Salva log
        log_path = None
        try:
            log_nome = f"Log_CIGS_{timestamp}.txt"
            with open(log_nome, 'w', encoding='utf-8') as f:
                f.write(self.txt_log.get("1.0", tk.END))
            log_path = os.path.abspath(log_nome)
        except:
            pass
        
        # ENVIA EMAIL COMPLETO!
        if stats['total'] > 0:
            self.email_manager.enviar_email_relatorio_completo(
                sistema=sis,
                stats=stats,
                csv_path=csv_path,
                log_path=log_path
            )
            self.log_visual("📧 Relatório enviado por email!")
        
        # Google Sheets
        if csv_d:
            try:
                dados_sheets = [[r[0], r[2], r[3], r[4], r[5]] for r in csv_d]
                self.sheets.atualizar_planilha(sis, dados_sheets)
                self.log_visual("📊 Planilha Google Atualizada.")
            except Exception as e:
                self.log_visual(f"⚠️  Erro Sheets: {e}")
        
        self.log_visual(">>> FIM RELATÓRIO <<<")

    def _atualizar_tree_relatorio(self, item_id, mensagem):
        """Atualiza árvore com resultado do relatório"""
        try:
            if self.infra_panel.tree.exists(item_id):
                valores = list(self.infra_panel.tree.item(item_id)['values'])
                if len(valores) >= 7:
                    valores[6] = mensagem
                    self.infra_panel.tree.item(item_id, values=valores)
        except:
            pass

    def btn_abortar(self):
        """Solicita confirmação e inicia aborto das operações"""
        if messagebox.askyesno("STOP", "Cancelar todas as operações?"):
            threading.Thread(target=self.worker_abortar).start()
            
    def worker_abortar(self):
        """Envia comando de aborto para todos os servidores"""
        count = 0
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            suc, msg = self.core.enviar_ordem_abortar(ip)
            if suc:
                count += 1
        self.log_visual(f"🛑 ABORTADO: {count} servidores cancelados.")

    # ==========================================
    # CONFIGURAÇÕES
    # ==========================================
    
    def janela_config_email(self):
        """Abre janela para configuração de email com múltiplos destinatários"""
        win = Toplevel(self.root)
        win.title("📧 Configuração de Email - CIGS")
        win.geometry("500x350")
        win.resizable(False, False)
        win.configure(bg="#ecf0f1")
        
        # Título
        tk.Label(win, text="CONFIGURAÇÃO DE NOTIFICAÇÕES", 
                font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50").grid(
                row=0, column=0, columnspan=2, pady=(15, 10))
        
        # Frame para credenciais
        f_creds = tk.LabelFrame(win, text="Credenciais SMTP", bg="#ecf0f1", 
                            font=("Arial", 10, "bold"))
        f_creds.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        f_creds.columnconfigure(1, weight=1)
        
        tk.Label(f_creds, text="Email:", bg="#ecf0f1").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        e1 = tk.Entry(f_creds, width=35)
        e1.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(f_creds, text="Senha:", bg="#ecf0f1").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        e2 = tk.Entry(f_creds, show="*", width=35)
        e2.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(f_creds, text="SMTP Server:", bg="#ecf0f1").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        e3 = tk.Entry(f_creds, width=35)
        e3.insert(0, "smtp.gmail.com")
        e3.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(f_creds, text="SMTP Port:", bg="#ecf0f1").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        e4 = tk.Entry(f_creds, width=35)
        e4.insert(0, "587")
        e4.grid(row=3, column=1, padx=5, pady=5)
        
        # Frame para destinatários
        f_dest = tk.LabelFrame(win, text="Destinatários (separados por ;)", 
                            bg="#ecf0f1", font=("Arial", 10, "bold"))
        f_dest.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        f_dest.columnconfigure(1, weight=1)
        
        tk.Label(f_dest, text="Para:", bg="#ecf0f1").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        e5 = tk.Entry(f_dest, width=45)
        e5.grid(row=0, column=1, padx=5, pady=5)
        
        # Carregar configurações existentes se houver
        creds = self.security.obter_credenciais()
        if creds:
            e1.insert(0, creds.get('email', ''))
            e2.insert(0, creds.get('senha', ''))
            e3.delete(0, tk.END)
            e3.insert(0, creds.get('server', 'smtp.gmail.com'))
            e4.delete(0, tk.END)
            e4.insert(0, creds.get('port', '587'))
            
            # Destinatários (pode estar em campo separado)
            destinatarios = creds.get('destinatarios', '')
            if destinatarios:
                e5.insert(0, destinatarios)
        
        # Botões
        f_buttons = tk.Frame(win, bg="#ecf0f1")
        f_buttons.grid(row=3, column=0, columnspan=2, pady=20)
        
        def salvar():
            # Salva credenciais
            self.security.salvar_credenciais(
                e1.get(), e2.get(), e3.get(), e4.get()
            )
            
            # Salva destinatários em arquivo separado ou no mesmo dict
            # Por simplicidade, vamos recarregar e adicionar
            creds = self.security.obter_credenciais()
            if creds:
                creds['destinatarios'] = e5.get()
                # Re-salva com destinatários
                self.security.salvar_credenciais(
                    creds['email'], creds['senha'], creds['server'], creds['port']
                )
                # TODO: Salvar destinatários em arquivo separado
            
            messagebox.showinfo("Sucesso", "Configurações salvas com segurança!")
            win.destroy()
        
        def testar():
            """Envia email de teste"""
            try:
                creds = {
                    'email': e1.get(),
                    'senha': e2.get(),
                    'server': e3.get(),
                    'port': e4.get()
                }
                
                msg = MIMEText("Este é um email de teste do CIGS.\n\nConfiguração SMTP funcionando corretamente!")
                msg['Subject'] = "🔧 CIGS - Teste de Configuração"
                msg['From'] = e1.get()
                msg['To'] = e1.get()
                
                server = smtplib.SMTP(e3.get(), int(e4.get()))
                server.starttls()
                server.login(e1.get(), e2.get())
                server.send_message(msg)
                server.quit()
                
                messagebox.showinfo("Sucesso", "Email de teste enviado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha no teste: {str(e)}")
        
        tk.Button(f_buttons, text="📧 Testar", command=testar,
                bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(f_buttons, text="💾 Salvar", command=salvar,
                bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(f_buttons, text="❌ Cancelar", command=win.destroy,
                bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                padx=15, pady=5).pack(side="left", padx=5)
    
    def show_about(self):
        """Exibe janela 'Sobre'"""
        messagebox.showinfo("CIGS", 
                           "Central de Comandos Integrados\n"
                           "Versão 3.7.3 (Estavel)\n"
                           "Desenvolvido por Gabriel Levi\n"
                           "Fortes Tecnologia - 2026")
    
    def enviar_email_relatorio(self, anexo, t, s, f):
        """
        Envia relatório por email
        anexo: caminho do arquivo CSV
        t: total de execuções
        s: sucessos
        f: falhas
        """
        c = self.security.obter_credenciais()
        if not c:
            self.log_visual("⚠️  Credenciais de email não configuradas.")
            return
            
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"Relatório CIGS {datetime.now().strftime('%d/%m/%Y')}"
            msg['From'] = c['email']
            msg['To'] = c['email']
            
            # Corpo do email
            corpo = f"""
            Relatório de Atualizações CIGS
            
            Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            Total de execuções: {t}
            Sucessos: {s}
            Falhas: {f}
            Taxa de sucesso: {round((s/t)*100, 1) if t > 0 else 0}%
            
            Arquivo em anexo: {anexo}
            """
            msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
            
            # Anexo
            with open(anexo, "rb") as a:
                p = MIMEBase("application", "octet-stream")
                p.set_payload(a.read())
                encoders.encode_base64(p)
                p.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(anexo)}"')
                msg.attach(p)
            
            # Envio
            server = smtplib.SMTP(c['server'], int(c['port']))
            server.starttls()
            server.login(c['email'], c['senha'])
            server.send_message(msg)
            server.quit()
            
            self.log_visual("📧 Email enviado com sucesso!")
            
        except Exception as e:
            self.log_visual(f"❌ Erro ao enviar email: {e}")
    
    def montar_aba_usuarios(self):
        """Constrói a interface de gestão de técnicos e administradores"""
        p = self.users_panel
        tk.Label(p, text="CENTRAL DE COMANDO - GESTÃO DE ACESSO", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=20)
        
        # Frame de Cadastro
        f_cad = tk.LabelFrame(p, text="Cadastrar Novo Operador", padx=20, pady=20)
        f_cad.pack(padx=20, fill="x")
        
        tk.Label(f_cad, text="Login:").grid(row=0, column=0, sticky="w")
        ent_user = tk.Entry(f_cad, width=30)
        ent_user.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(f_cad, text="Senha:").grid(row=1, column=0, sticky="w")
        ent_pass = tk.Entry(f_cad, width=30, show="*")
        ent_pass.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(f_cad, text="Patente:").grid(row=2, column=0, sticky="w")
        combo_role = ttk.Combobox(f_cad, values=["tecnico", "admin"], state="readonly", width=27)
        combo_role.current(0)
        combo_role.grid(row=2, column=1, padx=10, pady=5)
        
        def salvar():
            u, s, r = ent_user.get().strip(), ent_pass.get().strip(), combo_role.get()
            if not u or not s:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            sucesso, msg = self.db.criar_usuario(u, s, r)
            if sucesso:
                messagebox.showinfo("Sucesso", f"Operador {u} cadastrado com a patente {r}!")
                ent_user.delete(0, tk.END); ent_pass.delete(0, tk.END)
            else:
                messagebox.showerror("Erro", msg)

        tk.Button(f_cad, text="CADASTRAR OPERADOR", bg="#27ae60", fg="white", 
                  font=("Arial", 10, "bold"), command=salvar, padx=20).grid(row=3, column=0, columnspan=2, pady=15)
        
        tk.Label(p, text="Dica: Operadores com patente 'tecnico' não podem excluir servidores ou gerenciar outros usuários.", 
                 fg="gray", bg="#ecf0f1").pack(pady=10)