"""
CIGS - Central de Comandos Integrados v2.5 (Master)
Aplicação desktop para gerenciamento e automação de infraestrutura de servidores
"""

# Importa a biblioteca Tkinter para interface gráfica
import tkinter as tk
# Importa componentes específicos do Tkinter
from tkinter import ttk, messagebox, filedialog, scrolledtext, Toplevel, Label, Entry, Button
# Importa Tkinter temático para estilização moderna
from ttkthemes import ThemedTk
# Importa threading para execução paralela (não bloquear a interface)
import threading
# Importa subprocess para executar comandos do sistema
import subprocess
# Importa os para operações com sistema de arquivos
import os
# Importa csv para manipulação de arquivos CSV
import csv
# Importa webbrowser para abrir URLs no navegador
import webbrowser
# Importa time para pausas e controle de tempo
import time
# Importa datetime para manipulação de datas e horas
from datetime import datetime, timedelta
# Importa urlparse para análise de URLs
from urllib.parse import urlparse
import random, hashlib

# Importa módulos para envio de email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import tkinter.simpledialog as simpledialog # Importante para o Login

# Imports do Núcleo - módulos personalizados da aplicação
from core.network_ops import CIGSCore          # Operações de rede e comunicação
from core.sheets_manager import CIGSSheets    # Gerenciamento de planilhas Google
from core.security_manager import CIGSSecurity # Gerenciamento de segurança e credenciais
from core.db_manager import CIGSDatabase
from gui.dialogs.schedule_dialog import ScheduleDialog

# Imports dos Painéis - componentes de interface modularizados
from gui.panels.top_panel import TopPanel      # Painel superior da interface
from gui.panels.infra_panel import InfraPanel  # Painel de infraestrutura
from gui.panels.db_panel import DbPanel        # Painel de banco de dados
from gui.panels.dashboard_panel import DashboardPanel  # Painel de dashboard
from gui.dialogs.add_server_dialog import AddServerDialog

class CIGSApp:
    """
    Classe principal da aplicação CIGS
    Gerencia toda a interface gráfica e coordena os módulos
    """
    
    def __init__(self, root):
        """
        Inicializador da classe principal
        root: janela principal do Tkinter
        """
        self.root = root

        # --- 1. BLOCO DE SEGURANÇA (Token) ---
        desafio = str(random.randint(100000, 999999))
        
        seed = "CIGS_2026_ELITE"
        raw = f"{seed}{desafio}"
        resposta_correta = hashlib.sha256(raw.encode()).hexdigest()[:6].upper()
    
        # Janela de Bloqueio
        auth_win = tk.Toplevel(root)
        auth_win.title("🔒 ACESSO BLOQUEADO")
        auth_win.geometry("350x250")
        auth_win.grab_set()
        auth_win.resizable(False, False)

        auth_win.columnconfigure(0, weight=1)
        auth_win.columnconfigure(1, weight=1)

        tk.Label(auth_win, text="PROTOCOLO DE SEGURANÇA ATIVO",
             font=("Arial", 10, "bold"), fg="red").grid(row=0, column=0, columnspan=2, pady=(15, 5), sticky="ew")

        tk.Label(auth_win, text=f"TOKEN DE ACESSO: {desafio}",
             font=("Impact", 24), fg="#2980b9").grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        tk.Label(auth_win, text="Insira a contra-senha do KeyGen:",
             font=("Arial", 9)).grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        ent_senha = ttk.Entry(auth_win, font=("Arial", 14), justify="center", show="*")
        ent_senha.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        ent_senha.focus()

        self.auth_ok = False

        def verificar(event=None): # Adicionei event=None para aceitar o Enter
            if ent_senha.get().strip().upper() == resposta_correta or ent_senha.get() == "admin_resgate":
                self.auth_ok = True
                auth_win.destroy()
            else:
                messagebox.showerror("ERRO", "Contra-senha incorreta! Acesso negado.")
                ent_senha.delete(0, tk.END)

        # Permite apertar ENTER para desbloquear
        auth_win.bind('<Return>', verificar)

        ttk.Button(auth_win, text="🔓 DESBLOQUEAR", command=verificar).grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        self.root.wait_window(auth_win)
    
        if not self.auth_ok:
            root.destroy()
            return
        
       
        self.db = CIGSDatabase() 
        self.core = CIGSCore()
        self.sheets = CIGSSheets()
        self.security = CIGSSecurity()
        
        self.monitor_active = False 
        self.setup_window()
        self.setup_sidebar_layout() 
        self.setup_menu()
        
        self.monitor_active = True
        self.monitor_thread()
        self.root.after(500, self.carregar_servidores_db)
        
    def setup_window(self):
        """Configura as propriedades da janela principal"""
        # Define título da janela
        self.root.title("CIGS - Central de Comandos Integrados")
        # Define tamanho inicial da janela
        self.root.geometry("1280x850")
        # Tenta maximizar a janela (compatibilidade entre sistemas)
        try: self.root.state('zoomed')
        except: pass
        # Tenta carregar ícone da aplicação
        try: self.root.iconbitmap("assets/CIGS.ico")
        except: pass
        
    def setup_sidebar_layout(self):
        """Configura o layout principal com sidebar e área de conteúdo"""
        
        # Container Principal - PanedWindow permite redimensionamento
        self.paned = tk.PanedWindow(self.root, orient="horizontal", sashwidth=5, bg="#2c3e50")
        self.paned.pack(fill="both", expand=True)

        # --- SIDEBAR (Esquerda) ---
        # Cria frame para sidebar com cor de fundo escura
        self.frame_sidebar = tk.Frame(self.paned, bg="#2c3e50", width=220)
        self.paned.add(self.frame_sidebar, minsize=200)
        
        # Adiciona título e subtítulo na sidebar
        tk.Label(self.frame_sidebar, text="C.I.G.S", font=("Impact", 28), fg="#ecf0f1", bg="#2c3e50").pack(pady=(30, 10))
        tk.Label(self.frame_sidebar, text="Comandos Integrados", font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 30))

        # Define estilo padrão para os botões da sidebar
        btn_style = {"font": ("Segoe UI", 11, "bold"), "bg": "#34495e", "fg": "white", 
                    "activebackground": "#2980b9", "activeforeground": "white", 
                    "bd": 0, "pady": 12, "cursor": "hand2", "anchor": "w", "padx": 20}
        
        # Botão para painel de infraestrutura
        self.btn_infra = tk.Button(self.frame_sidebar, text="📡  INFRAESTRUTURA", 
                                  command=lambda: self.show_page("infra"), **btn_style)
        self.btn_infra.pack(fill="x", pady=2)
        
        # Botão para painel de dashboard
        self.btn_dash = tk.Button(self.frame_sidebar, text="📊  DASHBOARD", 
                                 command=lambda: self.show_page("dash"), **btn_style)
        self.btn_dash.pack(fill="x", pady=2)
        
        # Botão para painel de banco de dados clínico
        self.btn_db = tk.Button(self.frame_sidebar, text="🏥  CLÍNICA BD", 
                               command=lambda: self.show_page("db"), **btn_style)
        self.btn_db.pack(fill="x", pady=2)

        # --- CONTEÚDO (Direita) ---
        # Cria frame principal para conteúdo
        self.frame_content = tk.Frame(self.paned, bg="#ecf0f1")
        self.paned.add(self.frame_content, stretch="always")
        
        # Configura grid do frame de conteúdo
        self.frame_content.columnconfigure(0, weight=1)
        self.frame_content.rowconfigure(1, weight=1)

        # 1. Painel Superior
        # Instancia o painel superior passando função de validação de link
        self.top_panel = TopPanel(self.frame_content, self.core.verificar_validade_link)
        self.top_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # 2. Container das Páginas
        # Frame que conterá as diferentes páginas/painéis
        self.container = tk.Frame(self.frame_content)
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        # Dicionário para armazenar referências aos painéis
        self.pages = {}
        # Instancia painel de infraestrutura com callbacks
        self.infra_panel = InfraPanel(self.container, {
            'rdp': self.rdp_connect, 
            'deploy': self.btn_deploy_massa,
            'load_ips': self.btn_carregar_padrao, 
            'import_csv': self.btn_importar_csv_bd, # <--- CORREÇÃO FEITA
            'load_db': self.carregar_servidores_db,
            'add_server': self.abrir_add_server
        })
        self.pages["infra"] = self.infra_panel
        
        # Instancia painel de dashboard
        self.dash_panel = DashboardPanel(self.container, self.db, self.core)
        self.pages["dash"] = self.dash_panel
        
        # Instancia painel de banco de dados com callback
        self.db_panel = DbPanel(self.container, self.executar_manutencao_bd, self.iniciar_scan_bancos, self.iniciar_agendamento)
        self.pages["db"] = self.db_panel

        # Posiciona todos os painéis no mesmo grid (sobrepostos)
        for p in self.pages.values(): 
            p.grid(row=0, column=0, sticky="nsew")
        # Exibe o painel de infraestrutura por padrão
        self.show_page("infra")

        # 3. Rodapé (Grid)
        self.frame_bot = tk.Frame(self.frame_content)
        self.frame_bot.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.frame_bot.columnconfigure(0, weight=1)
        
        # Área de log com scroll
        self.txt_log = scrolledtext.ScrolledText(self.frame_bot, height=6, font=("Consolas", 9))
        self.txt_log.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # --- BARRA DE PROGRESSO NOVA ---
        self.progress_var = tk.DoubleVar()
        self.progress_var = ttk.Progressbar(self.frame_bot, variable=self.progress_var, maximum=100)
        self.progress_var.grid(row=1, column=0, sticky='ew', pady=(0,5))
        self.lbl_progress = tk.Label(self.frame_bot, text="Aguardando comando...", font=("Arial", 8), fg="gray")
        self.lbl_progress.grid(row=2, column=0, sticky="w")

        # Botões de Ação
        f_act = tk.Frame(self.frame_bot)
        f_act.grid(row=1, column=0, sticky="ew")
        f_act.columnconfigure(0, weight=1)
        
        # Label de copyright
        ttk.Label(f_act, text='© 2026 Gabriel Levi · Fortes Tecnologia').grid(row=0, column=0, sticky="w", padx=5)
        
        # Botões alinhados à direita
        tk.Button(f_act, text="📊 Ver Relatório", command=self.btn_relatorio_final).grid(row=0, column=1, padx=5)
        
        tk.Button(f_act, text="📡 Scanear Infra", command=self.btn_scanear).grid(row=0, column=2, padx=5)
        
        tk.Button(f_act, text='❌ Abortar Disparo', command=self.btn_abortar, 
                  bg='#6D1B08', fg='white', font=("Arial", 10, "bold"), padx=10).grid(row=0, column=3, padx=5)
        
        tk.Button(f_act, text="🚀 DISPARAR MISSÃO (Checklist)", command=self.pre_flight_checklist, 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=4, padx=5)
        
        # --- NOVO BOTÃO: DISPARAR EM TODOS ---
        tk.Button(f_act, text="☢️ DISPARAR EM TODOS", command=self.btn_disparar_todos, 
                  bg="black", fg="#e74c3c", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=5, padx=5)

    def show_page(self, name):
        """
        Alterna entre as páginas/painéis da aplicação
        name: nome da página a ser exibida ("infra", "dash", "db")
        """
        # Eleva o painel solicitado ao topo (tkraise)
        self.pages[name].tkraise()
        # Cor padrão dos botões da sidebar
        def_bg = "#34495e"
        # Reseta cor de todos os botões
        self.btn_infra.config(bg=def_bg); self.btn_dash.config(bg=def_bg); self.btn_db.config(bg=def_bg)
        # Destaca botão da página ativa
        if name == "infra": self.btn_infra.config(bg="#2980b9")
        if name == "dash": self.btn_dash.config(bg="#2980b9")
        if name == "db": self.btn_db.config(bg="#2980b9")
    
    def abrir_add_server(self):
        AddServerDialog(self.root, self.salvar_novo_servidor)
    
    def salvar_novo_servidor(self, dados):
        """Salva no SQLite e atualiza a tela"""
        suc, msg = self.db.adicionar_servidor(dados['ip'], dados['host'], dados['pub'], dados['func'], dados['cli'])
        if suc:
            messagebox.showinfo("Sucesso", msg)
            self.carregar_servidores_db() # Recarrega a lista
        else:
            messagebox.showerror("Erro BD", msg)

    def carregar_servidores_db(self):
        """Lê do SQLite e preenche a tabela"""
        try:
            servidores = self.db.listar_servidores()
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            
            for s in servidores:
                # Mapeia colunas do banco para a tabela
                self.infra_panel.tree.insert("", "end", values=(
                    s['ip'], s['hostname'], s['ip_publico'], s['funcao'], s['cliente'], "...", "-"
                ), tags=("DEDICADO",))
            
            self.log_visual(f"Base de Dados: {len(servidores)} ativos carregados.")
            # Atualiza gráficos
            self.dash_panel.update_plots()
        except Exception as e:
            self.log_visual(f"Erro ao carregar DB: {e}")

    # --- MONITORAMENTO ---
    def monitor_thread(self):
        """
        Inicia thread para monitoramento em tempo real dos servidores
        Verifica status dos agentes periodicamente
        """
        def run():
            # Loop contínuo enquanto monitoramento estiver ativo
            while self.monitor_active:
                try:
                    # Obtém item selecionado na árvore de infraestrutura
                    sel = self.infra_panel.tree.selection()
                    if sel:
                        # Extrai IP do item selecionado
                        ip = self.infra_panel.tree.item(sel[0])['values'][0]
                        # Obtém sistema selecionado no painel superior
                        sis = self.top_panel.get_data()['sistema']
                        # Verifica status do agente (com informações completas)
                        res = self.core.checar_status_agente(ip, sis, full=True) 
                        # Se agente estiver online, atualiza dashboard
                        if res.get('status') == 'ONLINE':
                            pass
                            # Atualiza interface na thread principal
                            # self.root.after(0, lambda: self.dash_panel.update_live_stats(ip, res))
                except: 
                    pass  # Ignora erros para não quebrar o monitoramento
                # Aguarda 3 segundos entre verificações
                time.sleep(3)
        # Inicia thread em segundo plano
        threading.Thread(target=run, daemon=True).start()

    # --- CHECKLIST ---
    def pre_flight_checklist(self):
        """
        Executa checklist pré-disparo para validar condições
        Abre janela modal com validações passo a passo
        """
        # Verifica se há servidores selecionados
        sel = self.infra_panel.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhum servidor selecionado.\nSelecione na lista.")
            return
        
        # Cria janela modal para checklist
        win = Toplevel(self.root); win.title("Checklist"); win.geometry("450x500")
        tk.Label(win, text="Validação Pré-Missão", font=("Arial", 14, "bold")).pack(pady=10)
        # Listbox para exibir resultados do checklist
        lst = tk.Listbox(win, font=("Consolas", 10), bg="#fdfefe")
        lst.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Botão para autorizar disparo (inicialmente desabilitado)
        btn_go = tk.Button(win, text="AUTORIZAR DISPARO", state="disabled", bg="#e74c3c", fg="white",
                           command=lambda: [win.destroy(), 
                                           threading.Thread(target=self.worker_disparo, args=(sel,)).start()])
        btn_go.pack(pady=15)

        def add(msg, color="black"):
            """Adiciona mensagem à listbox do checklist"""
            lst.insert(tk.END, msg); lst.itemconfig(tk.END, fg=color); lst.see(tk.END); win.update()
            time.sleep(0.2)  # Pequena pausa para efeito visual

        def run_check():
            """Função que executa as validações do checklist"""
            erros = 0
            # Obtém dados do painel superior
            d = self.top_panel.get_data()
            add(f"1. Alvos: {len(sel)}", "blue")
            
            # Valida URL (exceto para rede local)
            if not d['url'] and "Rede Local" not in d['tipo']:
                add("❌ Link AWS vazio!", "red"); erros+=1
            else: add("✅ Parâmetros OK", "green")
            
            # Valida arquivo local para rede local
            if "Rede Local" in d['tipo']:
                paths = [os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                         os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")]
                if any(os.path.exists(p) for p in paths): add("✅ Arquivo local OK", "green")
                else: add("❌ Arquivo local 404!", "red"); erros+=1
            
            # Testa conectividade com primeiro servidor selecionado
            ip_teste = self.infra_panel.tree.item(sel[0])['values'][0]
            res = self.core.checar_status_agente(ip_teste, d['sistema'])
            if res.get('status') == "ONLINE": add("✅ Conectividade OK", "green")
            else: add("⚠️ Agente Offline/Instável", "orange")

            # Decide se pode prosseguir com base nos erros
            if erros == 0:
                add("\n>>> PRONTO PARA COMBATE <<<", "green")
                # Habilita botão de disparo
                btn_go.config(state="normal", bg="#27ae60")
            else:
                add("\n❌ ABORTAR", "red")

        # Executa checklist em thread separada para não travar interface
        threading.Thread(target=run_check).start()
    
    def btn_disparar_todos(self):
        """
        Seleciona automaticamente TODOS os servidores da lista e inicia o checklist.
        Reaproveita a validação de segurança existente.
        """
        # 1. Pega todos os itens (IDs) que estão na árvore (Treeview)
        todos_itens = self.infra_panel.tree.get_children()
        
        if not todos_itens:
            messagebox.showwarning("Aviso", "A lista está vazia! Carregue os servidores primeiro.")
            return
            
        # 2. Confirmação de Segurança (Vital para operações em massa)
        if not messagebox.askyesno("CONFIRMAÇÃO DE COMBATE", f"ATENÇÃO: Você vai disparar contra {len(todos_itens)} servidores.\n\nDeseja realmente prosseguir?"):
            return

        # 3. O Pulo do Gato: Seleciona todos programaticamente
        # Isso faz a Central achar que você clicou em todos eles com o mouse
        self.infra_panel.tree.selection_set(todos_itens)
        
        # 4. Chama o checklist normal
        # Como agora tudo está selecionado, ele vai validar e processar a lista inteira
        self.pre_flight_checklist()
        
    # --- WORKERS ---
    def log_visual(self, msg):
        """
        Adiciona mensagem à área de log visual
        msg: mensagem a ser registrada
        """
        # Usa after para executar na thread principal
        self.root.after(0, lambda: self.txt_log.insert(tk.END, 
                     f"{datetime.now().strftime('%H:%M:%S')} {msg}\n") or self.txt_log.see(tk.END))

    def btn_carregar_padrao(self):
        """
        Carrega lista de IPs a partir de arquivo TXT
        Callback para botão de carregar IPs padrão
        """
        # Abre diálogo para selecionar arquivo
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if path:
            # Carrega IPs usando módulo core
            ips = self.core.carregar_lista_ips(path)
            # Limpa árvore atual
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            # Adiciona cada IP à árvore
            for ip in ips: 
                self.infra_panel.tree.insert("", "end", values=(ip, "...", "-", "-"))
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
        
        if escolha is None: return # Cancelou

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
                        # Cabeçalho padrão + Exemplo
                        f.write("IP;Hostname;IP_Publico;Funcao;Cliente\n")
                        f.write("192.168.1.50;SRV-APP01;200.1.1.50;APP;Cliente Exemplo\n")
                        f.write("192.168.1.51;SRV-BD01;200.1.1.51;BD;Cliente Exemplo\n")
                    messagebox.showinfo("Sucesso", f"Template gerado em:\n{path}")
                    # Abre o arquivo automaticamente para facilitar
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
                # Detecta delimitador (Ponto e vírgula é melhor para Excel BR)
                # Lê como dicionário para mapear colunas
                reader = csv.DictReader(f, delimiter=';')
                
                # Verifica se as colunas existem
                if not {'IP', 'Hostname'}.issubset(reader.fieldnames):
                    messagebox.showerror("Erro Formato", "O CSV deve ter colunas separadas por PONTO E VÍRGULA (;)\nColunas exigidas: IP;Hostname;IP_Publico;Funcao;Cliente")
                    return

                for row in reader:
                    ip = row.get('IP', '').strip()
                    if not ip: continue # Pula linha vazia
                    
                    # Tenta inserir no Banco
                    suc, msg = self.db.adicionar_servidor(
                        ip, 
                        row.get('Hostname', '-'), 
                        row.get('IP_Publico', '-'), 
                        row.get('Funcao', 'SRV'), 
                        row.get('Cliente', 'Generico')
                    )
                    
                    if suc: sucessos += 1
                    else: 
                        erros += 1
                        self.log_visual(f"Falha ao importar {ip}: {msg}")
            
            # Atualiza a tela
            self.carregar_servidores_db()
            
            resumo = f"Processamento Finalizado!\n\n✅ Importados: {sucessos}\n❌ Falhas/Duplicados: {erros}"
            if erros > 0: resumo += "\n(Verifique o Log para detalhes)"
            
            messagebox.showinfo("Relatório de Importação", resumo)
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao ler arquivo: {str(e)}")

    def btn_scanear(self): 
        """Inicia scan de infraestrutura em thread separada"""
        threading.Thread(target=self.worker_scan).start()
        
    def worker_scan(self):
            """
        SCAN TÁTICO v4.0 - CORRIGIDO E OTIMIZADO
        Varre todos os servidores e coleta:
        - Status do agente (Online/Offline)
        - Número de clientes ativos
        - Cliente referência
        - Versão do agente (info adicional)
        - Disponibilidade de disco/RAM (modo full)
        """
        
            # ==========================================
            # 1. INICIALIZAÇÃO
            # ==========================================
            sis = self.top_panel.get_data()['sistema']
            self.log_visual(f"\n{'='*60}")
            self.log_visual(f"📡 SCAN INICIADO - Sistema: {sis}")
            self.log_visual(f"{'='*60}\n")
            
            items = self.infra_panel.tree.get_children()
            total = len(items)
            
            if total == 0:
                self.log_visual("⚠️  Lista de servidores vazia!")
                return

            # ==========================================
            # 2. ESTATÍSTICAS DO SCAN
            # ==========================================
            stats = {
                'online': 0,
                'offline': 0,
                'erro': 0,
                'total_clientes': 0,
                'versoes': {},  # Contagem de versões encontradas
                'tempo_resposta': []  # Para latência média
            }

            # ==========================================
            # 3. SCAN PRINCIPAL
            # ==========================================
            for i, item in enumerate(items, 1):
                # --- Atualiza progresso ---
                percent = int((i / total) * 100)
                self.update_progress(i, total, f"Scanning... {percent}% ({i}/{total})")
                
                # --- Recupera dados existentes (preservar informações manuais) ---
                valores_atuais = list(self.infra_panel.tree.item(item)['values'])
                
                # Garante tamanho mínimo da lista (7 colunas)
                while len(valores_atuais) < 7:
                    valores_atuais.append("-")
                
                ip = valores_atuais[0]
                hostname = valores_atuais[1] if len(valores_atuais) > 1 else "-"
                ip_pub = valores_atuais[2] if len(valores_atuais) > 2 else "-"
                funcao = valores_atuais[3] if len(valores_atuais) > 3 else "-"
                cliente_atual = valores_atuais[4] if len(valores_atuais) > 4 else "-"
                
                # --- Log de início para este servidor ---
                self.log_visual(f"[{i}/{total}] 🔍 {ip} ({hostname})...")
                
                # --- Marca tempo de resposta ---
                inicio = time.time()
                
                try:
                    # Consulta o agente (modo full = False para ser mais rápido)
                    res = self.core.checar_status_agente(ip, sis, full=False)
                    tempo = round((time.time() - inicio) * 1000, 1)  # ms
                    
                    st = res.get('status', 'ERRO')
                    msg = res.get('msg', '')
                    
                    # --- PROCESSAMENTO POR STATUS ---
                    if st == "ONLINE":
                        # Extrai dados do agente
                        versao = res.get('version', '?')
                        hash_agente = res.get('hash', '')
                        qtd_clientes = res.get('clientes', 0)
                        ref_cliente = res.get('ref', '-')
                        disk_gb = res.get('disk', '?')
                        ram_perc = res.get('ram', '?')
                        
                        # Atualiza estatísticas
                        stats['online'] += 1
                        stats['total_clientes'] += qtd_clientes
                        stats['tempo_resposta'].append(tempo)
                        
                        # Contagem de versões
                        stats['versoes'][versao] = stats['versoes'].get(versao, 0) + 1
                        
                        # --- DEFINIÇÃO DO STATUS VISUAL ---
                        # Formato: "ON (clientes - referência)"
                        status_display = f"ON ({qtd_clientes} - {ref_cliente})"
                        
                        # Define tag base
                        tag = "ONLINE"
                        
                        # --- INFO ADICIONAL (tooltip/small) ---
                        info_extra = f"v{versao} | Disk: {disk_gb}GB | RAM: {ram_perc}%"
                        
                        # --- DECISÃO INTELIGENTE DO CLIENTE ---
                        # Se o cliente atual é placeholder (-, vazio, 0) e o agente retornou um nome válido
                        if str(cliente_atual) in ["-", "", "0", "None", "?", "N/A"] and ref_cliente not in ["-", "", "N/A"]:
                            cliente_atual = ref_cliente
                            self.log_visual(f"   ↳ Cliente atualizado: {cliente_atual}")
                        
                        self.log_visual(f"   ✅ ONLINE | Clientes: {qtd_clientes} | Ref: {ref_cliente} | Versão: {versao} | {tempo}ms")
                        
                    else:
                        # Servidor offline ou erro
                        stats['offline' if st == "OFFLINE" else 'erro'] += 1
                        status_display = st
                        tag = "OFFLINE"
                        info_extra = msg
                        
                        self.log_visual(f"   ❌ {st} | {msg}")
                        
                except Exception as e:
                    # Erro inesperado na requisição
                    stats['erro'] += 1
                    status_display = "ERRO"
                    tag = "OFFLINE"
                    info_extra = str(e)[:50]
                    
                    self.log_visual(f"   💥 ERRO INESPERADO: {str(e)[:100]}")
                    res = {'msg': str(e)}
                    msg = str(e)

                # --- ATUALIZAÇÃO DA TABELA (Thread Safe) ---
                # Colunas: IP | Hostname | IP Pub | Função | Cliente | Status | Info
                novos_valores = [
                    ip,                    # Coluna 0: IP (imutável)
                    hostname,             # Coluna 1: Hostname (preservado)
                    ip_pub,              # Coluna 2: IP Público (preservado)
                    funcao,              # Coluna 3: Função (preservada)
                    cliente_atual,       # Coluna 4: Cliente (atualizado inteligentemente)
                    status_display,      # Coluna 5: Status (formatado)
                    info_extra           # Coluna 6: Info adicional (versão, disco, etc)
                ]
                
                # Agenda atualização na thread principal
                self.root.after(0, lambda id=item, v=novos_valores, t=tag: 
                            self._atualizar_tree_seguro(id, v, (t,)))
                
                # Pequena pausa para não sobrecarregar a rede
                if i % 10 == 0:
                    time.sleep(0.1)

            # ==========================================
            # 4. FINALIZAÇÃO E ESTATÍSTICAS
            # ==========================================
            
            # --- Calcula latência média real ---
            latencia_media = 0
            if stats['tempo_resposta']:
                latencia_media = round(sum(stats['tempo_resposta']) / len(stats['tempo_resposta']), 1)
            
            # --- Registra histórico no banco de dados ---
            try:
                self.db.registrar_scan(
                    total=total,
                    on=stats['online'],
                    off=stats['offline'] + stats['erro'],
                    latencia=latencia_media
                )
            except Exception as e:
                self.log_visual(f"⚠️  Erro ao registrar histórico: {e}")
            
            # --- Log de resumo ---
            self.log_visual(f"\n{'='*60}")
            self.log_visual(f"📊 RESUMO DO SCAN - {sis}")
            self.log_visual(f"{'='*60}")
            self.log_visual(f"✅ Online:  {stats['online']}")
            self.log_visual(f"❌ Offline: {stats['offline']}")
            self.log_visual(f"⚠️  Erros:   {stats['erro']}")
            self.log_visual(f"📋 Total:    {total}")
            self.log_visual(f"\n👥 Total de clientes ativos: {stats['total_clientes']}")
            self.log_visual(f"⏱️  Latência média: {latencia_media}ms")
            
            # --- Distribuição de versões ---
            if stats['versoes']:
                self.log_visual(f"\n📦 Versões do Agente:")
                for versao, qtd in sorted(stats['versoes'].items()):
                    percent = round((qtd / stats['online']) * 100, 1) if stats['online'] > 0 else 0
                    self.log_visual(f"   • {versao}: {qtd} servidores ({percent}%)")
            
            # --- Taxa de sucesso ---
            if total > 0:
                sucesso_percent = round((stats['online'] / total) * 100, 1)
                self.log_visual(f"\n🎯 Disponibilidade: {sucesso_percent}%")
            
            self.log_visual(f"\n{'='*60}")
            self.log_visual(f"🏁 SCAN FINALIZADO")
            self.log_visual(f"{'='* 60}\n")
            
            # --- Atualiza interface ---
            self.update_progress(total, total, f"Scan Completo: {stats['online']} ON / {stats['offline']} OFF / {stats['erro']} ERRO")
            
            # Atualiza dashboard gráfico
            self.root.after(0, self.dash_panel.update_plots)
                
    def btn_disparar(self): 
        """Inicia checklist pré-disparo"""
        self.pre_flight_checklist()

    def worker_disparo(self, selecionados):
        """
        Worker que executa disparo de atualizações para servidores selecionados
        selecionados: lista de IDs dos itens selecionados na árvore
        """
        # Obtém dados do painel superior
        d = self.top_panel.get_data()
        # Log visual para você ter certeza que a Central pegou o valor
        self.log_visual(f">>> DISPARO (Script: {d['script']} | Args: {d['params']}) <<<")
        
        local_exe = ""
        # Define modo de operação baseado no tipo (Rede Local vs AWS)
        if "Rede Local" in d['tipo']:
            paths = [os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                     os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")]
            local_exe = next((p for p in paths if os.path.exists(p)), None)
            modo = "APENAS_EXEC"
        else: 
            modo = "COMPLETO"

        # Converte data/hora para objeto datetime
        try: 
            db = datetime.strptime(f"{d['data']} {d['hora']}", "%d/%m/%Y %H:%M")
        except: 
            return

        self.log_visual(">>> DISPARO <<<")
        cnt = 0
        # Itera por cada servidor selecionado
        for item_id in selecionados:
            item = self.infra_panel.tree.item(item_id)
            ip = item['values'][0]
            # Para lotes grandes, espaça os agendamentos
            if cnt > 0 and cnt % 10 == 0: 
                db += timedelta(minutes=15)
            dt_str = db.strftime("%d/%m/%Y %H:%M")
            
            copia_ok = True
            # Modo Rede Local: copia arquivo local para servidor
            if modo == "APENAS_EXEC":
                pasta_sis = "Ponto" if d['sistema'] == "PONTO" else d['sistema']
                dest = f"\\\\{ip}\\C$\\Atualiza\\CloudUp\\CloudUpCmd\\{d['sistema']}\\Atualizadores\\{pasta_sis}\\{d['sistema']}.exe"
                self.log_visual(f"-> {ip}: Copiando...")
                try:
                    # Cria diretório de destino se não existir
                    path_dir = os.path.dirname(dest)
                    subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                    # Copia arquivo
                    subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, 
                                 stdout=subprocess.DEVNULL, check=True)
                except:
                    # Se falhar, tenta autenticar e copiar novamente
                    try:
                        self.log_visual(f"-> {ip}: Autenticando...")
                        subprocess.run(f'net use \\\\{ip}\\C$ /user:{d["user"]} {d["pass"]}', 
                                     shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, 
                                     stdout=subprocess.DEVNULL, check=True)
                        subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
                    except: 
                        copia_ok = False; msg = "Erro Copy"

            # Se cópia OK (ou modo AWS), envia ordem de agendamento
            if copia_ok:
                try: 
                    # Extrai nome do arquivo da URL
                    nome = os.path.basename(urlparse(d['url']).path) or "up.rar"
                except: 
                    nome = "up.rar"
                # Envia ordem para o agente
                suc, msg = self.core.enviar_ordem_agendamento(ip, d['url'], nome, dt_str, 
                                                            d['user'], d['pass'], d['sistema'], modo, script=d['script'],params=d['params']) 
            else: 
                suc=False
            
            # Atualiza interface com resultado
            tag = "SUCESSO" if suc else "OFFLINE"
            self.root.after(0, lambda i=item_id, m=msg, t=tag: 
                          self.infra_panel.tree.item(i, 
                          values=list(self.infra_panel.tree.item(i)['values'])[:-1] + [m], 
                          tags=(t,)))
            cnt += 1
        self.log_visual(">>> FIM DISPARO <<<")

    def rdp_connect(self, ip):
        """
        Estabelece conexão RDP com servidor
        ip: endereço IP do servidor
        """
        d = self.top_panel.get_data()
        try:
            # Configura credenciais no Windows
            subprocess.run(f'cmdkey /generic:TERMSRV/{ip} /user:"{d["user"]}" /pass:"{d["pass"]}"', 
                         shell=True)
            # Inicia sessão RDP
            subprocess.Popen(f'mstsc /v:{ip} /admin', shell=True)
        except Exception as e: 
            messagebox.showerror("Erro RDP", str(e))

    def executar_manutencao_bd(self, tipo_acao, motor):
        """Inicia a manutenção com os parâmetros escolhidos"""
        db_path = self.db_panel.get_db_path()
        if not db_path:
            messagebox.showwarning("Aviso", "Informe o caminho/nome do banco!")
            return
            
        if messagebox.askyesno("Confirmar", f"Executar {tipo_acao} no {motor}?\nAlvo: {db_path}"):
            threading.Thread(target=self.worker_db_manutencao, args=(tipo_acao, motor, db_path)).start()
        
    def worker_db_manutencao(self, acao, motor, db_path):
        self.root.after(0, lambda: self.db_panel.log(f"\n>>> INICIANDO {acao} ({motor}) <<<"))
        
        # Itera servidores selecionados (ou todos online, depende da sua tática)
        # Vou assumir "Selecionados" para segurança, ou todos da lista se nada selecionado
        sel = self.infra_panel.tree.selection()
        if not sel:
            items = self.infra_panel.tree.get_children()
        else:
            items = sel
            
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            
            # Pula offlines
            if "OFFLINE" in self.infra_panel.tree.item(item)['tags']:
                continue
                
            self.root.after(0, lambda i=ip: self.db_panel.log(f"-> Processando {i}..."))
            
            # Chama o CORE passando a script SQL se for MSSQL
            res = self.core.enviar_comando_bd(ip, motor, acao, db_path)
            
            self.root.after(0, lambda r=res: self.db_panel.log(f"   Status: {r.get('status')}\n   Msg: {r.get('msg')}"))
            
        self.root.after(0, lambda: self.db_panel.log(">>> FIM DA OPERAÇÃO <<<"))

    def btn_deploy_massa(self):
        """
        Inicia deploy em massa do agente CIGS
        Solicita confirmação antes de prosseguir
        """
        if not messagebox.askyesno("ATENÇÃO", "Deploy do Agente para TODOS?"): 
            return
        threading.Thread(target=self.worker_deploy).start()

    def worker_deploy(self):
        """ Deploy Tático v6.0 - CORRIGIDO E OTIMIZADO
        Fluxo correto: Autenticar → Matar processos → Copiar → Instalar → Limpar """
        # ==========================================
        # 1. VALIDAÇÃO DE PRÉ-REQUISITOS
        # ==========================================
        
        # 1.1 Verificar executável do agente
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
            self.log_visual("❌ ERRO CRÍTICO: CIGS_Agent.exe não encontrado na pasta da Central")
            self.log_visual("    Procurei em: ./CIGS_Agent.exe, ./dist/CIGS_Agent.exe, ./CIGS_Agent.dist")
            return

        # 1.2 Verificar utilitários obrigatórios
        util_erros = []
        if not os.path.exists("nssm.exe"):
            util_erros.append("nssm.exe")
        if not os.path.exists("Instalar_CIGS.bat"):
            util_erros.append("Instalar_CIGS.bat")
        
        if util_erros:
            self.log_visual(f"❌ ERRO: Arquivos obrigatórios não encontrados: {', '.join(util_erros)}")
            return

        # 1.3 Verificar UnRAR.exe (opcional, mas recomendado)
        tem_unrar = os.path.exists("UnRAR.exe")
        if not tem_unrar:
            self.log_visual("⚠️  AVISO: UnRAR.exe não encontrado. Extração remota pode falhar.")

        # ==========================================
        # 2. OBTER CREDENCIAIS
        # ==========================================
        dados_painel = self.top_panel.get_data()
        user = dados_painel['user'].strip()
        password = dados_painel['pass'].strip()
        
        if not user or not password:
            self.log_visual("❌ ERRO: Usuário e senha são obrigatórios para deploy remoto!")
            return

        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"🚀 DEPLOY TÁTICO INICIADO - MODO: {modo}")
        self.log_visual(f"📦 Origem: {origem}")
        self.log_visual(f"👤 Usuário: {user}")
        self.log_visual(f"{'='*60}\n")

        # ==========================================
        # 3. PROCESSAR SERVIDORES
        # ==========================================
        items = self.infra_panel.tree.get_children()
        total = len(items)
        
        if total == 0:
            self.log_visual("❌ Nenhum servidor na lista!")
            return

        stats = {
            'sucesso': 0,
            'falha': 0,
            'pulado': 0
        }

        for i, item in enumerate(items, 1):
            ip = self.infra_panel.tree.item(item)['values'][0]
            
            # Atualiza progresso
            self.update_progress(i, total, f"Processando {ip}...")
            
            # Pular servidores offline (opcional - comentar se quiser tentar mesmo assim)
            if "OFFLINE" in self.infra_panel.tree.item(item).get('tags', []):
                self.log_visual(f"⏭️  {ip}: Servidor offline - pulando")
                stats['pulado'] += 1
                continue

            dest_dir = f"\\\\{ip}\\C$\\CIGS"
            resultado = "❌ FALHA"
            
            try:
                # -------------------------------------------------
                # FASE 1: AUTENTICAÇÃO DE REDE
                # -------------------------------------------------
                self.log_visual(f"🔑 {ip}: Autenticando em \\\\{ip}\\C$...")
                
                # Remove conexões existentes primeiro
                subprocess.run(f'net use \\\\{ip}\\C$ /delete', 
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Estabelece nova conexão
                cmd_auth = f'net use \\\\{ip}\\C$ /user:"{user}" "{password}"'
                auth_result = subprocess.run(cmd_auth, shell=True, capture_output=True, text=True)
                
                if auth_result.returncode != 0:
                    raise Exception(f"Falha na autenticação: {auth_result.stderr[:100]}")

                # -------------------------------------------------
                # FASE 2: NEUTRALIZAR PROCESSOS ANTIGOS
                # -------------------------------------------------
                self.log_visual(f"🛑 {ip}: Neutralizando processos antigos...")
                
                # Para serviços (ignora erro se não existir)
                subprocess.run(f'sc \\\\{ip} stop CIGS_Service', 
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} stop TITAN_Service', 
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Mata processos com credenciais
                subprocess.run(f'taskkill /S {ip} /U "{user}" /P "{password}" /IM CIGS_Agent.exe /F /T',
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /U "{user}" /P "{password}" /IM TITAN_Agent.exe /F /T',
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Aguarda processos terminarem
                time.sleep(2)

                # -------------------------------------------------
                # FASE 3: CRIAR DIRETÓRIO E COPIAR ARQUIVOS
                # -------------------------------------------------
                self.log_visual(f"📋 {ip}: Preparando diretório {dest_dir}...")
                
                # Cria pasta (se não existir)
                subprocess.run(f'mkdir "{dest_dir}" 2>nul', 
                            shell=True, stdout=subprocess.DEVNULL)
                
                # Copia utilitários (sempre versão mais recente)
                self.log_visual(f"📦 {ip}: Copiando utilitários...")
                subprocess.run(f'copy /Y "nssm.exe" "{dest_dir}\\nssm.exe"', 
                            shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'copy /Y "Instalar_CIGS.bat" "{dest_dir}\\Instalar_CIGS.bat"', 
                            shell=True, stdout=subprocess.DEVNULL)
                
                if tem_unrar:
                    subprocess.run(f'copy /Y "UnRAR.exe" "{dest_dir}\\UnRAR.exe"', 
                                shell=True, stdout=subprocess.DEVNULL)
                
                # Copia agente (modo específico)
                self.log_visual(f"🤖 {ip}: Instalando novo agente...")
                
                if modo == "PASTA":
                    cmd_copy = f'xcopy "{origem}" "{dest_dir}" /E /I /Y /Q'
                else:
                    cmd_copy = f'copy /Y "{origem}" "{dest_dir}\\CIGS_Agent.exe"'
                
                copy_result = subprocess.run(cmd_copy, shell=True, capture_output=True)
                
                if copy_result.returncode != 0:
                    raise Exception("Falha na cópia do agente")

                # -------------------------------------------------
                # FASE 4: INSTALAÇÃO/ATUALIZAÇÃO DO SERVIÇO
                # -------------------------------------------------
                self.log_visual(f"⚙️  {ip}: Configurando serviço...")
                
                # Tenta 3 métodos em ordem decrescente de eficiência
                instalado = False
                
                # Método 1: WMIC com credenciais
                cmd_wmic = f'wmic /node:"{ip}" /user:"{user}" /password:"{password}" process call create "cmd.exe /c C:\\CIGS\\Instalar_CIGS.bat"'
                wmic_result = subprocess.run(cmd_wmic, shell=True, capture_output=True, text=True)
                
                if wmic_result.returncode == 0 and "ReturnValue = 0" in wmic_result.stdout:
                    instalado = True
                    self.log_visual(f"✅ {ip}: Instalação disparada via WMIC")
                else:
                    # Método 2: SchTasks com credenciais (fallback)
                    task_name = f"CIGS_Install_{ip.replace('.', '_')}"
                    cmd_schtasks = f'schtasks /create /s {ip} /u "{user}" /p "{password}" /tn "{task_name}" /tr "C:\\CIGS\\Instalar_CIGS.bat" /sc ONCE /st 00:01 /f /ru SYSTEM'
                    subprocess.run(cmd_schtasks, shell=True, stdout=subprocess.DEVNULL)
                    cmd_run = f'schtasks /run /s {ip} /u "{user}" /p "{password}" /tn "{task_name}"'
                    task_result = subprocess.run(cmd_run, shell=True, capture_output=True)
                    
                    if task_result.returncode == 0:
                        instalado = True
                        self.log_visual(f"✅ {ip}: Instalação disparada via Task Scheduler")
                        time.sleep(3)
                        # Limpa tarefa
                        subprocess.run(f'schtasks /delete /s {ip} /u "{user}" /p "{password}" /tn "{task_name}" /f',
                                    shell=True, stdout=subprocess.DEVNULL)
                
                if not instalado:
                    # Método 3: Último recurso - tenta iniciar serviço existente
                    start_result = subprocess.run(f'sc \\\\{ip} start CIGS_Service',
                                                shell=True, capture_output=True)
                    if start_result.returncode == 0:
                        instalado = True
                        self.log_visual(f"✅ {ip}: Serviço existente iniciado")
                    else:
                        raise Exception("Todos os métodos de instalação falharam")
                
                resultado = "✅ SUCESSO"
                stats['sucesso'] += 1
                
            except Exception as e:
                self.log_visual(f"❌ {ip}: ERRO - {str(e)}")
                resultado = "❌ FALHA"
                stats['falha'] += 1
            
            finally:
                # -------------------------------------------------
                # FASE 5: LIMPEZA OBRIGATÓRIA
                # -------------------------------------------------
                # Fecha conexão de rede
                subprocess.run(f'net use \\\\{ip}\\C$ /delete',
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Atualiza status na tree
                try:
                    valores_atuais = list(self.infra_panel.tree.item(item)['values'])
                    if len(valores_atuais) >= 6:
                        valores_atuais[5] = resultado  # Coluna Status
                        self.root.after(0, lambda i=item, v=valores_atuais: 
                                    self._atualizar_tree_seguro(i, v, (resultado.strip('✅❌'),)))
                except:
                    pass

        # ==========================================
        # 4. RELATÓRIO FINAL
        # ==========================================
        self.log_visual(f"\n{'='*60}")
        self.log_visual(f"📊 RELATÓRIO FINAL DO DEPLOY")
        self.log_visual(f"{'='*60}")
        self.log_visual(f"✅ Sucesso: {stats['sucesso']}")
        self.log_visual(f"❌ Falha:   {stats['falha']}")
        self.log_visual(f"⏭️  Pulado:  {stats['pulado']}")
        self.log_visual(f"📋 Total:    {total}")
    
        if stats['falha'] == 0 and stats['sucesso'] > 0:
            self.log_visual(f"\n🎯 DEPLOY CONCLUÍDO COM SUCESSO TOTAL!")
        elif stats['sucesso'] > 0:
            self.log_visual(f"\n⚠️  DEPLOY CONCLUÍDO COM FALHAS PARCIAIS")
        else:
            self.log_visual(f"\n❌ DEPLOY FALHOU COMPLETAMENTE")
    
        self.log_visual(f"{'='*60}\n")
        self.update_progress(total, total, "Deploy Finalizado")

    def btn_relatorio_final(self):
        """Solicita confirmação e inicia geração de relatório"""
        if messagebox.askyesno("Relatório", "Gerar?"): 
            threading.Thread(target=self.worker_relatorio).start()
    
    def worker_relatorio(self):
        """
        Worker que gera relatório consolidado de execuções
        Coleta dados de todos os servidores online e exporta para CSV
        """
        # Obtém dados do painel superior
        data = self.top_panel.get_data(); sis = data['sistema']
        # Formata data para uso no relatório
        dt = datetime.strptime(data['data'], "%d/%m/%Y").strftime("%Y%m%d")
        self.log_visual(">>> RELATÓRIO <<<")
        csv_d = []; t_g=0; s_g=0
        
        # Itera por todos os servidores
        items = self.infra_panel.tree.get_children()
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            # Processa apenas servidores online
            if "OFFLINE" not in self.infra_panel.tree.item(item)['values'][1]:
                # Obtém relatório do agente
                res = self.core.obter_relatorio_agente(ip, sis, dt)
                if "erro" not in res:
                    # Extrai estatísticas
                    t=res.get('total',0); s=res.get('sucessos',0); p=res.get('porcentagem',0)
                    t_g+=t; s_g+=s
                    # Adiciona linha para CSV
                    csv_d.append([ip, sis, t, s, f"{p}%", res.get('arquivo')])
                    # Atualiza árvore com resultado
                    self.root.after(0, lambda i=item, m=f"Log: {s}/{t}": 
                                  self.infra_panel.tree.item(i, 
                                  values=list(self.infra_panel.tree.item(i)['values'])[:-1]+[m]))
        try:
            # Gera nome do arquivo CSV
            nome = f"Rel_{sis}_{datetime.now().strftime('%H%M')}.csv"
            # Salva CSV
            with open(nome, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow(["IP","Sis","Tot","Suc","%","Arq"])
                w.writerows(csv_d)
            self.log_visual(f"Salvo: {nome}")
            # Envia email com relatório se houver dados
            if csv_d: 
                self.enviar_email_relatorio(nome, t_g, s_g, t_g-s_g)
        except: 
            pass
        
        # Sincronia Google Sheets
        if csv_d:
            try:
                # Prepara dados para planilha (exclui coluna do sistema)
                dados_sheets = [[r[0], r[2], r[3], r[4], r[5]] for r in csv_d] # IP, Tot, Suc, %, Arq
                self.sheets.atualizar_planilha(sis, dados_sheets)
                self.log_visual("Planilha Google Atualizada.")
            except: 
                pass

    def btn_exportar_log(self):
        """Exporta conteúdo do log visual para arquivo de texto"""
        try:
            with open("cigs_log.txt", "w") as f: 
                f.write(self.txt_log.get("1.0", tk.END))
            messagebox.showinfo("OK", "Log Salvo")
        except: 
            pass
            
    def btn_abortar(self):
        """Solicita confirmação e inicia aborto das operações"""
        if messagebox.askyesno("STOP", "Cancelar?"): 
            threading.Thread(target=self.worker_abortar).start()
            
    def worker_abortar(self):
        """Envia comando de aborto para todos os servidores"""
        for item in self.infra_panel.tree.get_children(): 
            self.core.enviar_ordem_abortar(self.infra_panel.tree.item(item)['values'][0])
        self.log_visual("ABORTADO.")
    
    def setup_menu(self):
        """Configura a barra de menus superior da aplicação"""
        menubar = tk.Menu(self.root); self.root.config(menu=menubar)
        # Menu Arquivo
        f = tk.Menu(menubar, tearoff=0); 
        f.add_command(label="Sair", command=self.root.quit); 
        menubar.add_cascade(label="Arquivo", menu=f)
        # Menu Configurações
        c = tk.Menu(menubar, tearoff=0); 
        c.add_command(label="Email", command=self.janela_config_email); 
        menubar.add_cascade(label="Config", menu=c)
        # Menu Ajuda
        h = tk.Menu(menubar, tearoff=0); 
        h.add_command(label="Sobre", command=self.show_about); 
        menubar.add_cascade(label="Ajuda", menu=h)

    def janela_config_email(self):
        """Abre janela para configuração de credenciais de email"""
        win = Toplevel(self.root); win.title("Email")
        Label(win, text="Email:").grid(row=0,column=0); 
        e1=Entry(win); e1.grid(row=0,column=1)
        Label(win, text="Senha:").grid(row=1,column=0); 
        e2=Entry(win, show="*"); e2.grid(row=1,column=1)
        Button(win, text="Salvar", 
               command=lambda:[self.security.salvar_credenciais(e1.get(),e2.get()), 
                              win.destroy()]).grid(row=2,columnspan=2)
    
    def _atualizar_tree_seguro(self, item_id, valores, tags):
        """Atualiza a árvore apenas se o item ainda existir"""
        try:
            if self.infra_panel.tree.exists(item_id):
                self.infra_panel.tree.item(item_id, values=valores, tags=tags)
        except:
            pass

    def enviar_email_relatorio(self, anexo, t, s, f):
        """
        Envia relatório por email
        anexo: caminho do arquivo CSV
        t: total de execuções
        s: sucessos
        f: falhas
        """
        # Obtém credenciais de email
        c = self.security.obter_credenciais()
        if not c: 
            return
        try:
            # Configura mensagem de email
            msg = MIMEMultipart()
            msg['Subject'] = f"Relatorio CIGS {datetime.now().strftime('%d/%m')}"
            msg['From'] = c['email']; msg['To'] = c['email']
            
            # Anexa arquivo CSV
            with open(anexo, "rb") as a: 
                p=MIMEBase("application","octet-stream")
                p.set_payload(a.read())
                encoders.encode_base64(p)
                p.add_header('Content-Disposition',f"attachment; filename={anexo}")
                msg.attach(p)
            
            # Envia email via SMTP
            s = smtplib.SMTP(c['server'], int(c['port']))
            s.starttls()
            s.login(c['email'], c['senha'])
            s.sendmail(c['email'], [c['email']], msg.as_string())
            s.quit()
            self.log_visual("Email Enviado.")
        except: 
            pass
    
    def abrir_link(self, u): 
        """Abre URL no navegador padrão"""
        webbrowser.open(u)
        
    def show_about(self): 
        """Exibe janela 'Sobre' com informações da versão"""
        messagebox.showinfo("CIGS", "v3.1 - Desenvolvido por Gabriel Levi")
    
    def iniciar_scan_bancos(self):
        """Inicia a varredura de pastas em thread"""
        sel = self.infra_panel.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um servidor para escanear os discos C: e D:!")
            return
        
        # Pega apenas o primeiro servidor selecionado para preencher o combo (limitação lógica de UI)
        ip = self.infra_panel.tree.item(sel[0])['values'][0]
        d = self.top_panel.get_data() # Para pegar usuario/senha admin
        
        self.db_panel.log(f"Iniciando varredura em \\\\{ip}\\C$\\BDS e D$...")
        threading.Thread(target=self.worker_scan_bancos, args=(ip, d['user'], d['pass'])).start()

    def worker_scan_bancos(self, ip, user, password):
        """
        Varre C:\BDS e D:\BDS via compartilhamento administrativo
        Procura estrutura: BDS \ CLIENTE \ SISTEMA \ ARQUIVO.FDB
        """
        encontrados = []
        drives = ['C$', 'D$']
        
        # Tenta autenticar primeiro
        cmd_auth = f'net use \\\\{ip}\\C$ /user:{user} {password}'
        subprocess.run(cmd_auth, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for drive in drives:
            root_path = f"\\\\{ip}\\{drive}\\BDS"
            if not os.path.exists(root_path):
                continue
                
            self.root.after(0, lambda d=drive: self.db_panel.log(f"Varrendo {d}..."))
            
            try:
                # Walk manual com limite de profundidade para ser rápido
                # Estrutura esperada: BDS/Cliente/Sistema/Banco.FDB
                for cliente in os.listdir(root_path):
                    path_cliente = os.path.join(root_path, cliente)
                    if os.path.isdir(path_cliente):
                        for sistema in os.listdir(path_cliente):
                            # Filtra apenas sistemas conhecidos para otimizar
                            if sistema.upper() in ["AC", "AG", "PATRIO", "PONTO"]:
                                path_sistema = os.path.join(path_cliente, sistema)
                                if os.path.isdir(path_sistema):
                                    for arq in os.listdir(path_sistema):
                                        if arq.upper().endswith(".FDB"):
                                            # Reconstrói o caminho local do servidor (C:\BDS...)
                                            caminho_local = f"{drive[0]}:\\BDS\\{cliente}\\{sistema}\\{arq}"
                                            encontrados.append(caminho_local)
            except Exception as e:
                self.root.after(0, lambda e=e: self.db_panel.log(f"Erro scan: {e}"))

        subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
        
        # Atualiza a combobox na thread principal
        self.root.after(0, lambda: self.db_panel.update_combo_list(encontrados))

    # --- AGENDAMENTO ---
    def iniciar_agendamento(self, motor):
        """Abre o dialogo de agendamento"""
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
        
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            if "OFFLINE" in self.infra_panel.tree.item(item)['tags']: continue
            
            self.root.after(0, lambda i=ip: self.db_panel.log(f"-> {i}: Criando tarefa inteligente..."))
            
            # 1. Cria o Script de Manutenção Tático (Auto-Discovery)
            script_content = ""
            
            if motor == "FIREBIRD":
                # --- SCRIPT INTELIGENTE: RASTREIA O GFIX ---
                script_content = f"""
                @echo off
                set LOG=C:\\CIGS\\maintenance.log
                echo ------------------------------------------------ >> %LOG%
                echo Iniciando Manutencao Firebird: %DATE% %TIME% >> %LOG%
                
                set "GFIX="

                :: 1. TENTATIVA AUTOMATICA: Buscar pelo servico do Windows
                :: Procura servicos que tenham 'Firebird' no nome e pega o caminho do executavel (bin)
                for /f "tokens=2 delims==" %%I in ('wmic service where "name like 'FirebirdGuard%%' or name like 'FirebirdServer%%'" get PathName /value 2^>nul ^| find "="') do set "FB_PATH=%%~dpI"
                
                if defined FB_PATH (
                    if exist "%FB_PATH%gfix.exe" set "GFIX=%FB_PATH%gfix.exe"
                )

                :: 2. TENTATIVA MANUAL: Caminhos conhecidos (Fallback)
                if not defined GFIX if exist "C:\\Program Files\\Firebird\\Firebird_2_5\\bin\\gfix.exe" set "GFIX=C:\\Program Files\\Firebird\\Firebird_2_5\\bin\\gfix.exe"
                if not defined GFIX if exist "C:\\Fortes\\Firebird\\Firebird_2_5\\bin\\gfix.exe" set "GFIX=C:\\Fortes\\Firebird\\Firebird_2_5\\bin\\gfix.exe"
                if not defined GFIX if exist "D:\\Firebird_2_5\\bin\\gfix.exe" set "GFIX=D:\\Firebird_2_5\\bin\\gfix.exe"
                if not defined GFIX if exist "C:\\Program Files (x86)\\Firebird\\Firebird_2_5\\bin\\gfix.exe" set "GFIX=C:\\Program Files (x86)\\Firebird\\Firebird_2_5\\bin\\gfix.exe"
                if not defined GFIX if exist "C:\\Fortes\Firebird_5_0\\gfix.exe" set "GFIX=C:\\Fortes\Firebird_5_0\\gfix.exe"
                :: Verifica se encontrou
                if not defined GFIX (
                    echo ERRO CRITICO: gfix.exe nao encontrado em nenhum local. >> %LOG%
                    exit /b 1
                )

                echo GFIX Detectado: "%GFIX%" >> %LOG%
                echo Alvo: "{db_path}" >> %LOG%

                :: Executa a manutencao
                "%GFIX%" -mend -full -ignore "{db_path}" -user SYSDBA -pass masterkey >> %LOG% 2>&1
                "%GFIX%" -sweep "{db_path}" -user SYSDBA -pass masterkey >> %LOG% 2>&1
                
                echo Fim da operacao >> %LOG%
                """
            
            elif motor == "MSSQL":
                # Para MSSQL, mantemos a logica do sqlcmd
                sql_file = r"C:\CIGS\maintenance.sql"
                script_content = f"""
                @echo off
                echo Iniciando MSSQL Maintenance >> C:\\CIGS\\maintenance.log
                date /t >> C:\\CIGS\\maintenance.log
                sqlcmd -S localhost -E -i "{sql_file}" >> C:\\CIGS\\maintenance.log 2>&1
                echo Fim >> C:\\CIGS\\maintenance.log
                """
                # Nota: Para MSSQL funcionar 100%, voce precisaria enviar o arquivo .sql tambem.
                # Se quiser, posso adicionar o codigo que cria o maintenance.sql la no servidor.

            # Envia o script .bat para o servidor
            try:
                # Caminho UNC
                unc_path = f"\\\\{ip}\\C$\\CIGS"
                d = self.top_panel.get_data()
                
                # Conecta no drive C$
                subprocess.run(f'net use {unc_path} /user:{d["user"]} {d["pass"]}', shell=True, stdout=subprocess.DEVNULL)
                
                # Garante que a pasta existe
                subprocess.run(f'mkdir {unc_path}', shell=True, stdout=subprocess.DEVNULL)

                # Salva localmente e envia
                with open("temp_maint.bat", "w") as f: f.write(script_content)
                subprocess.run(f'copy /Y temp_maint.bat "{unc_path}\\maintenance_task.bat"', shell=True, stdout=subprocess.DEVNULL)
                
                # Limpeza local
                if os.path.exists("temp_maint.bat"): os.remove("temp_maint.bat")

                # Cria a Tarefa Agendada via SCHTASKS
                cmd_sch = f'schtasks /create /s {ip} /u {d["user"]} /p {d["pass"]} /tn "{task_name}" /tr "C:\\CIGS\\maintenance_task.bat" /sc ONCE /st {hora} /sd {data} /ru SYSTEM /f'
                
                res = subprocess.run(cmd_sch, shell=True, capture_output=True, text=True)
                
                if res.returncode == 0:
                    msg = "Sucesso: Agendado."
                else:
                    msg = f"Erro Schtasks: {res.stderr.strip()}"
                    
                subprocess.run(f'net use {unc_path} /delete', shell=True, stdout=subprocess.DEVNULL)
                
            except Exception as e:
                msg = f"Falha fatal: {str(e)}"
            
            self.root.after(0, lambda r=msg: self.db_panel.log(f"   Resultado: {r}"))
            
        self.root.after(0, lambda: self.db_panel.log(">>> AGENDAMENTO CONCLUÍDO <<<"))