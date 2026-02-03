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
# Importa módulos para envio de email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Imports do Núcleo - módulos personalizados da aplicação
from core.network_ops import CIGSCore          # Operações de rede e comunicação
from core.sheets_manager import CIGSSheets    # Gerenciamento de planilhas Google
from core.security_manager import CIGSSecurity # Gerenciamento de segurança e credenciais

# Imports dos Painéis - componentes de interface modularizados
from gui.panels.top_panel import TopPanel      # Painel superior da interface
from gui.panels.infra_panel import InfraPanel  # Painel de infraestrutura
from gui.panels.db_panel import DbPanel        # Painel de banco de dados
from gui.panels.dashboard_panel import DashboardPanel  # Painel de dashboard


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
        # Armazena referência à janela principal
        self.root = root
        # Instancia o núcleo de operações de rede
        self.core = CIGSCore()
        # Instancia o gerenciador de planilhas
        self.sheets = CIGSSheets()
        # Instancia o gerenciador de segurança
        self.security = CIGSSecurity()
        
        # Flag para controle do monitoramento em tempo real
        self.monitor_active = False 
        # Configura a janela principal
        self.setup_window()
        # Configura o layout com sidebar
        self.setup_sidebar_layout() 
        # Configura o menu superior
        self.setup_menu()
        
        # Inicia o monitoramento em tempo real
        self.monitor_active = True
        # Inicia thread de monitoramento
        self.monitor_thread()

    def setup_window(self):
        """Configura as propriedades da janela principal"""
        # Define título da janela
        self.root.title("CIGS - Central de Comandos Integrados v2.5 (Master)")
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
            'load_csv': self.btn_carregar_dedicados
        })
        self.pages["infra"] = self.infra_panel
        
        # Instancia painel de dashboard
        self.dash_panel = DashboardPanel(self.container)
        self.pages["dash"] = self.dash_panel
        
        # Instancia painel de banco de dados com callback
        self.db_panel = DbPanel(self.container, self.btn_check_db)
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
        
        # Botões de Ação
        f_act = tk.Frame(self.frame_bot)
        f_act.grid(row=1, column=0, sticky="ew")
        f_act.columnconfigure(0, weight=1)
        
        # Label de copyright
        ttk.Label(f_act, text='© 2026 Gabriel Levi · Fortes Tecnologia').grid(row=0, column=0, sticky="w", padx=5)
        
        # Botões alinhados à direita
        tk.Button(f_act, text="📊 Ver Relatório", command=self.btn_relatorio_final).grid(row=0, column=1, padx=5)
        tk.Button(f_act, text="📡 Scanear Infra", command=self.btn_scanear).grid(row=0, column=2, padx=5)
        tk.Button(f_act, text="🚀 DISPARAR MISSÃO (Checklist)", command=self.pre_flight_checklist, 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=3, padx=5)

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
                            # Atualiza interface na thread principal
                            self.root.after(0, lambda: self.dash_panel.update_live_stats(ip, res))
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

    def btn_carregar_dedicados(self):
        """
        Carrega lista de servidores dedicados a partir de arquivo CSV
        Callback para botão de carregar dedicados
        """
        # Abre diálogo para selecionar arquivo CSV
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            try:
                ips = []
                # Lê arquivo CSV
                with open(path, newline='', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f); next(reader, None)  # Pula cabeçalho
                    for row in reader:
                        # Valida formato de IP
                        if row and len(row)>0 and row[0].count('.')==3:
                            # Adiciona IP e nome do cliente
                            ips.append((row[0].strip(), row[1] if len(row)>1 else "Dedicado"))
                # Limpa árvore atual
                self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
                # Adiciona servidores dedicados com tag especial
                for ip, cli in ips:
                    self.infra_panel.tree.insert("", "end", values=(ip, "...", cli, "-"), tags=("DEDICADO",))
                self.log_visual(f"Dedicados: {len(ips)}")
            except Exception as e: 
                messagebox.showerror("Erro CSV", str(e))

    def btn_scanear(self): 
        """Inicia scan de infraestrutura em thread separada"""
        threading.Thread(target=self.worker_scan).start()
        
    def worker_scan(self):
        """
        Worker que executa scan de todos os servidores na lista
        Verifica status de cada agente e atualiza interface
        """
        # Obtém sistema selecionado
        sis = self.top_panel.get_data()['sistema']
        self.log_visual(f">>> SCAN ({sis}) <<<")
        # Obtém todos os itens da árvore
        items = self.infra_panel.tree.get_children()
        # Contadores para estatísticas
        on=0; off=0; crit=0
        
        # Calcula hash do agente local para comparação
        h_model = "N/A"
        if os.path.exists("CIGS_Agent.exe"):
            try:
                import hashlib; h = hashlib.md5()
                with open("CIGS_Agent.exe", "rb") as f: 
                    h.update(f.read())
                h_model = h.hexdigest()
            except: pass

        # Itera por cada servidor na lista
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            cli_orig = self.infra_panel.tree.item(item)['values'][2]
            # Verifica status do agente
            res = self.core.checar_status_agente(ip, sis)
            
            st = res.get('status')
            tag = "OFFLINE"
            # Processa resultado
            if st == "ONLINE":
                st = f"ON ({res.get('version','?')})"
                tag = "ONLINE"; on+=1
                # Verifica se versão do agente difere do modelo
                if h_model != "N/A" and res.get('hash') != h_model:
                    tag = "CRITICO"; st = "⚠️ vDIF"; crit+=1
                cli = res.get('clientes', '-')
            else:
                off+=1; cli = cli_orig
            
            # Prepara valores para atualização
            vals = (ip, st, cli, res.get('msg',''))
            # Atualiza interface na thread principal
            self.root.after(0, lambda i=item, v=vals, t=tag: 
                          self.infra_panel.tree.item(i, values=v, tags=(t,)))
        
        self.log_visual(">>> FIM SCAN <<<")
        # Atualiza estatísticas no dashboard
        self.root.after(0, lambda: self.dash_panel.update_stats(len(items), on, off, crit))

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
                                                            d['user'], d['pass'], d['sistema'], modo)
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

    def btn_check_db(self): 
        """Inicia verificação de banco de dados em thread separada"""
        threading.Thread(target=self.worker_db_check).start()
        
    def worker_db_check(self):
        """Worker que verifica status do banco de dados em todos os servidores online"""
        # Limpa painel de DB e adiciona cabeçalho
        self.root.after(0, lambda: self.db_panel.clear() or self.db_panel.log("=== CHECK DB ==="))
        sis = self.top_panel.get_data()['sistema']
        # Itera por todos os servidores
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            # Verifica apenas servidores online
            if "OFFLINE" not in self.infra_panel.tree.item(item)['values'][1]:
                self.root.after(0, lambda i=ip: self.db_panel.log(f"Check {i}..."))
                # Verifica banco de dados
                r = self.core.verificar_banco(ip, sis)
                # Define ícone baseado no resultado
                icon = "✅" if "OK" in r.get('status','') else "❌"
                # Adiciona resultado ao log
                self.root.after(0, lambda t=f"{icon} {r.get('status')}\n{r.get('log')}\n---": 
                              self.db_panel.log(t))

    def btn_deploy_massa(self):
        """
        Inicia deploy em massa do agente CIGS
        Solicita confirmação antes de prosseguir
        """
        if not messagebox.askyesno("ATENÇÃO", "Deploy do Agente para TODOS?"): 
            return
        threading.Thread(target=self.worker_deploy).start()

    def worker_deploy(self):
        """
        Worker que executa deploy do agente CIGS em todos os servidores
        Para serviços antigos, copia novos arquivos e configura serviço
        """
        # Verifica se arquivo/pasta do agente existe
        if os.path.exists("CIGS_Agent.dist"): 
            m="PASTA"; o="CIGS_Agent.dist"
        elif os.path.exists("CIGS_Agent.exe"): 
            m="ARQUIVO"; o="CIGS_Agent.exe"
        else: 
            self.log_visual("Falta Agente"); return
        # Verifica se nssm.exe existe (para criação de serviço)
        if not os.path.exists("nssm.exe"): 
            self.log_visual("Falta nssm"); return

        self.log_visual(f">>> DEPLOY ({m}) <<<")
        # Itera por todos os servidores
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            dest = f"\\\\{ip}\\C$\\CIGS"
            try:
                # Para serviços antigos
                subprocess.run(f'sc \\\\{ip} stop TITAN_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} delete TITAN_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} stop CIGS_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /IM TITAN_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /IM CIGS_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL)
                time.sleep(2)  # Aguarda processos terminarem
                
                # Cria diretório CIGS no servidor
                subprocess.run(f'mkdir "{dest}"', shell=True, stdout=subprocess.DEVNULL)
                
                # Copia arquivos do agente
                if m=="PASTA": 
                    subprocess.run(f'xcopy "{o}" "{dest}" /E /I /Y', shell=True, stdout=subprocess.DEVNULL)
                else: 
                    subprocess.run(f'copy /Y "{o}" "{dest}\\CIGS_Agent.exe"', shell=True, stdout=subprocess.DEVNULL)
                
                # Copia utilitários necessários
                subprocess.run(f'copy /Y "nssm.exe" "{dest}\\nssm.exe"', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'copy /Y "UnRAR.exe" "{dest}\\UnRAR.exe"', shell=True, stdout=subprocess.DEVNULL)
                
                # Instala e configura serviço Windows
                rmt = r"C:\CIGS\CIGS_Agent.exe"
                subprocess.run(f'wmic /node:"{ip}" process call create "C:\\CIGS\\nssm.exe install CIGS_Service \"{rmt}\""', 
                             shell=True, stdout=subprocess.DEVNULL)
                time.sleep(1)
                subprocess.run(f'wmic /node:"{ip}" process call create "C:\\CIGS\\nssm.exe set CIGS_Service AppDirectory \"C:\\CIGS\""', 
                             shell=True, stdout=subprocess.DEVNULL)
                
                # Inicia serviço ou executa diretamente se falhar
                if subprocess.run(f'sc \\\\{ip} start CIGS_Service', shell=True, 
                                stdout=subprocess.DEVNULL).returncode != 0:
                     subprocess.run(f'wmic /node:"{ip}" process call create "{rmt}"', 
                                  shell=True, stdout=subprocess.DEVNULL)
                self.log_visual(f"-> {ip}: OK")
            except Exception as e: 
                self.log_visual(f"-> {ip}: Falha {e}")
        self.log_visual(">>> FIM DEPLOY <<<")

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
        messagebox.showinfo("CIGS", "v2.5 Master")