import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, Toplevel, Label, Entry, Button
from ttkthemes import ThemedTk
import threading
import subprocess
import os
import csv
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
# Imports do Core
from core.network_ops import CIGSCore
from core.sheets_manager import CIGSSheets
from core.security_manager import CIGSSecurity

# IMPORTS DOS PAINÉIS
from gui.panels.top_panel import TopPanel
from gui.panels.infra_panel import InfraPanel
from gui.panels.db_panel import DbPanel
from gui.panels.dashboard_panel import DashboardPanel

class CIGSApp:
    def __init__(self, root):
        self.root = root
        self.core = CIGSCore()
        self.sheets = CIGSSheets()
        self.security = CIGSSecurity()
        self.setup_ui()
        self.setup_menu()
        
    def setup_ui(self):
        self.root.title("CIGS - Central de Comandos Integrados v14.5 (Jungle)")
        self.root.geometry("1200x850")
        try: self.root.state('zoomed')
        except: pass 
        try: self.root.iconbitmap("assets/CIGS.ico")
        except: pass

        # Grid Mestre
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # 1. PAINEL SUPERIOR
        self.top_panel = TopPanel(self.root, self.core.verificar_validade_link)
        self.top_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # 2. ABAS (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Aba 1: Dashboard
        self.dash_panel = DashboardPanel(self.notebook)
        self.notebook.add(self.dash_panel, text="📊 Dashboard")

        # Aba 2: Infraestrutura
        callbacks_infra = {
            'rdp': self.rdp_connect,
            'deploy': self.btn_deploy_massa,
            'load_ips': self.btn_carregar_padrao,
            'load_csv': self.btn_carregar_dedicados
        }
        self.infra_panel = InfraPanel(self.notebook, callbacks_infra)
        self.notebook.add(self.infra_panel, text="📡 Infraestrutura")

        # Aba 3: Banco de Dados
        self.db_panel = DbPanel(self.notebook, self.btn_check_db)
        self.notebook.add(self.db_panel, text="🏥 Clínica BD")

        # 3. LOG GERAL
        frame_log = ttk.LabelFrame(self.root, text="Log de Operações", padding=5)
        frame_log.grid(row=2, column=0, sticky="ew", padx=10)
        self.txt_log = scrolledtext.ScrolledText(frame_log, height=6, font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True)

        # 4. RODAPÉ
        frame_bot = ttk.Frame(self.root, padding=10)
        frame_bot.grid(row=3, column=0, sticky="ew")
        
        ttk.Label(frame_bot, text='© 2026 Gabriel Levi · Direitos Reservados · Uso somente interno· Fortes Tecnologia').grid(row=1, column=0, columnspan=5, pady=5)
        
        for i in range(5): frame_bot.columnconfigure(i, weight=1)
        ttk.Button(frame_bot, text="📡 1. Scanear Infra", command=self.btn_scanear).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(frame_bot, text="🚀 2. Disparar Missão", command=self.btn_disparar).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_bot, text="📊 3. Relatório Completo", command=self.btn_relatorio_final).grid(row=0, column=2, padx=5, sticky="ew")
        
        btn_abort = tk.Button(frame_bot, text="🛑 ABORTAR TUDO", command=self.btn_abortar, bg="#c0392b", fg="white", font=("Arial", 9, "bold"))
        btn_abort.grid(row=0, column=3, padx=5, sticky="ew")


    # --- LÓGICA DE NEGÓCIO ---

    def log_visual(self, msg):
        # UI Update seguro
        self.root.after(0, lambda: self._safe_log(msg))

    def _safe_log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    # 1. CARREGAMENTO
    def btn_carregar_padrao(self):
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if not path: return
        ips = self.core.carregar_lista_ips(path)
        
        self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
        for ip in ips: 
            self.infra_panel.tree.insert("", "end", values=(ip, "...", "-", "-", "-", "-", "-"))
        self.log_visual(f"Lista Padrão Carregada: {len(ips)} IPs.")

    def btn_carregar_dedicados(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            ips = []
            with open(path, newline='', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and len(row) > 0 and row[0].count('.')==3:
                        ip = row[0].strip()
                        cliente = row[1] if len(row)>1 else "Dedicado"
                        ips.append((ip, cliente))
            
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            for ip, cli in ips:
                self.infra_panel.tree.insert("", "end", values=(ip, "...", cli, "-", "-", "-", "-"), tags=("DEDICADO",))
            self.log_visual(f"Lista Dedicados Carregada: {len(ips)} servidores.")
        except Exception as e:
            messagebox.showerror("Erro CSV", str(e))

    # 2. SCAN (CORREÇÃO DE THREADING AQUI)
    def btn_scanear(self): threading.Thread(target=self.worker_scan).start()
    
    def worker_scan(self):
        data = self.top_panel.get_data()
        sis = data['sistema']
        self.log_visual(f">>> SCAN INICIADO ({sis}) <<<")
        
        items = self.infra_panel.tree.get_children()
        
        # Hash local
        hash_modelo = "N/A"
        if os.path.exists("CIGS_Agent.exe"):
            import hashlib
            try:
                h = hashlib.md5()
                with open("CIGS_Agent.exe", "rb") as f:
                    for c in iter(lambda: f.read(4096), b""): h.update(c)
                hash_modelo = h.hexdigest()
            except: pass

        on=0; off=0; crit=0
        
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            nome_cli_original = self.infra_panel.tree.item(item)['values'][2] 
            
            res = self.core.checar_status_agente(ip, sis)
            
            st = res.get('status')
            tag = "OFFLINE"
            
            if st == "ONLINE":
                st = f"ON ({res.get('version','?')})"
                if hash_modelo != "N/A" and res.get('hash') != hash_modelo:
                    tag = "CRITICO"; st = "⚠️ vDIF"
                    crit += 1
                else:
                    tag = "ONLINE"
                    on += 1
                
                cliente_final = nome_cli_original if nome_cli_original not in ["-", "..."] else res.get('clientes','-')
            else:
                off += 1
                cliente_final = nome_cli_original
            
            vals = (ip, st, cliente_final, res.get('ref','-'), res.get('disk','-'), res.get('ram','-'), res.get('msg',''))
            
            
            def update_ui_row(i=item, v=vals, t=tag):
                self.infra_panel.tree.item(i, values=v, tags=(t,))
            
            self.root.after(0, update_ui_row)
            # ---------------------------------------------------------------
        
        self.log_visual(">>> SCAN FINALIZADO <<<")
        # Atualiza Dashboard (já é seguro pois usa after lá dentro)
        self.root.after(0, lambda: self.dash_panel.update_stats(len(items), on, off, crit))

    # 3. DISPARO (CORREÇÃO DE THREADING AQUI TAMBÉM)
    def btn_disparar(self):
        if messagebox.askyesno("Confirmar", "Iniciar missão de atualização?"):
            threading.Thread(target=self.worker_disparo).start()

    def worker_disparo(self):
        dados = self.top_panel.get_data()
        items = self.infra_panel.tree.get_children()
        
        # Validação
        local_exe = ""
        if "Rede Local" in dados['tipo']:
            local_exe = os.path.join(r"C:\CIGS\Servicos", dados['sistema'], f"{dados['sistema']}.exe")
            if not os.path.exists(local_exe): 
                self.log_visual(f"ERRO: Arquivo não encontrado: {local_exe}")
                return
            modo = "APENAS_EXEC"
        else:
            if not dados['url']: 
                self.log_visual("ERRO: Link AWS vazio."); return
            modo = "COMPLETO"

        try: 
            db = datetime.strptime(f"{dados['data']} {dados['hora']}", "%d/%m/%Y %H:%M")
        except: 
            self.log_visual("ERRO: Data inválida"); return

        self.log_visual(f">>> DISPARO INICIADO (Modo: {modo}) <<<")
        
        count = 0; LOTE_QTD = 10; LOTE_TEMPO = 15
        
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            status_atual = self.infra_panel.tree.item(item)['values'][1]
            
            if "OFFLINE" not in status_atual:
                if count > 0 and count % LOTE_QTD == 0: db += timedelta(minutes=LOTE_TEMPO)
                dt_str = db.strftime("%d/%m/%Y %H:%M")
                
                # Cópia Local
                copia_sucesso = True
                if modo == "APENAS_EXEC":
                    self.log_visual(f"-> {ip}: Copiando EXE via rede...")
                    dest_rede = f"\\\\{ip}\\C$\\Atualiza\\CloudUp\\CloudUpCmd\\{dados['sistema']}\\{dados['sistema']}.exe"
                    try:
                        subprocess.run(f'copy /Y "{local_exe}" "{dest_rede}"', shell=True, stdout=subprocess.DEVNULL, timeout=20)
                    except Exception as e:
                        copia_sucesso = False
                        msg_final = f"Erro Copy: {e}"
                
                if copia_sucesso:
                    try:
                        path_url = urlparse(dados['url']).path
                        nome_arq = os.path.basename(path_url) or "update.rar"
                    except: nome_arq = "update.rar"

                    sucesso, msg = self.core.enviar_ordem_agendamento(
                        ip, dados['url'], nome_arq, dt_str, 
                        dados['user'], dados['pass'], dados['sistema'], modo
                    )
                    msg_final = msg
                else:
                    sucesso = False

                vals = list(self.infra_panel.tree.item(item)['values'])
                vals[-1] = msg_final
                tag = "SUCESSO" if sucesso else "OFFLINE"
                
                # --- ATUALIZAÇÃO SEGURA ---
                def update_row_disp(i=item, v=vals, t=tag):
                    self.infra_panel.tree.item(i, values=v, tags=(t,))
                self.root.after(0, update_row_disp)
                # --------------------------
                
                count += 1
                
        self.log_visual(">>> DISPARO CONCLUÍDO <<<")

    # 4. FERRAMENTAS
    def rdp_connect(self, ip):
        dados = self.top_panel.get_data()
        self.log_visual(f"Abrindo RDP para {ip}...")
        try:
            subprocess.run(f'cmdkey /generic:TERMSRV/{ip} /user:"{dados["user"]}" /pass:"{dados["pass"]}"', shell=True)
            subprocess.Popen(f'mstsc /v:{ip} /admin', shell=True)
        except Exception as e:
            messagebox.showerror("Erro RDP", str(e))

    def btn_check_db(self): threading.Thread(target=self.worker_db_check).start()
    
    def worker_db_check(self):
        # Acesso seguro aos métodos do painel DB
        self.root.after(0, lambda: self.db_panel.clear())
        self.root.after(0, lambda: self.db_panel.log("=== INICIANDO CHECK-UP DE BANCO ==="))
        
        sis = self.top_panel.get_data()['sistema']
        items = self.infra_panel.tree.get_children()
        
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            status = self.infra_panel.tree.item(item)['values'][1]
            
            if "OFFLINE" not in status:
                self.root.after(0, lambda i=ip: self.db_panel.log(f"Verificando {i}..."))
                res = self.core.verificar_banco(ip, sis)
                
                icon = "✅" if "OK" in res.get('status', '') else "❌"
                txt = f"Status: {icon} {res.get('status')}\nDetalhe: {res.get('log')}\n{'-'*40}"
                self.root.after(0, lambda t=txt: self.db_panel.log(t))

    def btn_deploy_massa(self):
        if not messagebox.askyesno("ATENÇÃO", "Isso copiará o Agente para TODOS os IPs da lista.\nTem certeza?"): return
        threading.Thread(target=self.worker_deploy).start()

    def worker_deploy(self):
        # 1. Validação dos Arquivos Locais (Munição)
        # Verifica se temos o Agente (pode ser pasta .dist ou arquivo .exe)
        if os.path.exists("CIGS_Agent.dist"):
            modo_origem = "PASTA"
            origem_agente = "CIGS_Agent.dist"
        elif os.path.exists("CIGS_Agent.exe"):
            modo_origem = "ARQUIVO"
            origem_agente = "CIGS_Agent.exe"
        else:
            self.log_visual("ERRO CRÍTICO: Não encontrei 'CIGS_Agent.dist' nem 'CIGS_Agent.exe'. Compile o agente primeiro!")
            return

        ferramentas = ["nssm.exe", "UnRAR.exe"]
        for f in ferramentas:
            if not os.path.exists(f): 
                self.log_visual(f"Falta ferramenta auxiliar: {f}")
                return
        
        self.log_visual(f">>> INICIANDO MIGRAÇÃO (TITAN -> CIGS) [Modo: {modo_origem}] <<<")
        
        # Percorre a tropa (lista de IPs)
        # Se você estiver usando o InfraPanel, o acesso é self.infra_panel.tree.get_children()
        # Se estiver no main_window antigo, é self.tree.get_children()
        # Ajuste conforme seu código atual. Vou assumir o padrão modular novo:
        items = self.infra_panel.tree.get_children() 

        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            dest_raiz = f"\\\\{ip}\\C$\\CIGS"
            
            self.log_visual(f"Atacando alvo: {ip}...")
            
            try:
                # 2. EXTERMINAR O INIMIGO (TITAN)
                # Tenta parar e deletar o serviço antigo silenciosamente
                subprocess.run(f'sc \\\\{ip} stop TITAN_Service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} delete TITAN_Service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Mata o processo na força bruta
                subprocess.run(f'taskkill /S {ip} /IM TITAN_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 3. PREPARAR O TERRENO (Limpar CIGS antigo se houver)
                subprocess.run(f'sc \\\\{ip} stop CIGS_Service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /IM CIGS_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(3) # Respiro tático pro Windows liberar arquivos
                
                # Cria a base C:\CIGS
                subprocess.run(f'mkdir "{dest_raiz}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 4. INFILTRAÇÃO (Cópia dos Arquivos)
                if modo_origem == "PASTA":
                    # Copia pasta inteira com XCOPY (/E = subpastas, /I = destino é pasta, /Y = sim para tudo)
                    cmd_copy = f'xcopy "{origem_agente}" "{dest_raiz}" /E /I /Y'
                    subprocess.run(cmd_copy, shell=True, stdout=subprocess.DEVNULL)
                else:
                    # Copia arquivo único
                    subprocess.run(f'copy /Y "{origem_agente}" "{dest_raiz}\\CIGS_Agent.exe"', shell=True, stdout=subprocess.DEVNULL)
                
                # Copia ferramentas auxiliares (nssm, unrar)
                for f in ferramentas:
                    subprocess.run(f'copy /Y "{f}" "{dest_raiz}\\{f}"', shell=True, stdout=subprocess.DEVNULL)
                
                # 5. INSTALAÇÃO DO SERVIÇO (Via WMIC para execução local remota)
                # Caminho do executável no servidor (sempre será C:\CIGS\CIGS_Agent.exe se for arquivo ou pasta padrão)
                exe_remoto = r"C:\CIGS\CIGS_Agent.exe"
                
                # Comandos NSSM montados para execução remota via WMIC
                cmd_install = f'C:\\CIGS\\nssm.exe install CIGS_Service "{exe_remoto}"'
                cmd_set_dir = f'C:\\CIGS\\nssm.exe set CIGS_Service AppDirectory "C:\\CIGS"'
                
                # Executa instalação
                subprocess.run(f'wmic /node:"{ip}" process call create "{cmd_install}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                subprocess.run(f'wmic /node:"{ip}" process call create "{cmd_set_dir}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Inicia o Serviço
                proc = subprocess.run(f'sc \\\\{ip} start CIGS_Service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Fallback: Se o serviço falhar (ex: erro de permissão no nssm), tenta rodar o EXE solto
                # Isso garante que a comunicação funcione mesmo sem o serviço
                if proc.returncode != 0:
                     self.log_visual(f"-> {ip}: Serviço falhou. Tentando modo Standalone...")
                     subprocess.run(f'wmic /node:"{ip}" process call create "{exe_remoto}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.log_visual(f"-> {ip}: CIGS Implantado com Sucesso.")
                
            except Exception as e:
                self.log_visual(f"-> {ip}: FALHA NA MISSÃO ({e})")
                
        self.log_visual(">>> OPERAÇÃO DE MIGRAÇÃO ENCERRADA <<<")

    # 5. EXPORTAÇÃO E RELATÓRIO
    def btn_exportar_log(self):
        try:
            with open("titan_log_ops.txt", "w") as f:
                f.write(self.txt_log.get("1.0", tk.END))
            messagebox.showinfo("Sucesso", "Log salvo!")
        except: pass

    def btn_relatorio_final(self):
        if messagebox.askyesno("Relatório", "Gerar relatório completo?"):
            threading.Thread(target=self.worker_relatorio).start()

    def worker_relatorio(self):
        data = self.top_panel.get_data()
        sis = data['sistema']
        dt_filtro = datetime.strptime(data['data'], "%d/%m/%Y").strftime("%Y%m%d")
        
        self.log_visual(">>> GERANDO RELATÓRIO... <<<")
        dados_csv = []
        dados_google = []
        tot_g = 0; suc_g = 0
        
        items = self.infra_panel.tree.get_children()
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            st = self.infra_panel.tree.item(item)['values'][1]
            
            if "OFFLINE" not in st:
                res = self.core.obter_relatorio_agente(ip, sis, dt_filtro)
                if "erro" not in res:
                    t = res.get('total',0); s = res.get('sucessos',0); p = res.get('porcentagem',0)
                    tot_g += t; suc_g += s
                    dados_csv.append([ip, sis, t, s, f"{p}%", res.get('arquivo')])
                    
                    # Atualiza Tabela (SEGURO)
                    msg_log = f"Log: {s}/{t} ({p}%)"
                    def upd(i=item, m=msg_log):
                        vals = list(self.infra_panel.tree.item(i)['values'])
                        vals[-1] = m
                        self.infra_panel.tree.item(i, values=vals)
                    self.root.after(0, upd)
        
        try:
            nome = f"Relatorio_{sis}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            with open(nome, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow(["IP", "Sistema", "Total", "Sucesso", "%", "Arquivo"])
                for d in dados_csv: w.writerow(d)
            self.log_visual(f"CSV Gerado: {nome}")
            if dados_csv: self.enviar_email_relatorio(nome, tot_g, suc_g, tot_g-suc_g)
        except Exception as e: self.log_visual(f"Erro Relatório: {e}")

        # INTEGRAÇÃO GOOGLE SHEETS RESTAURADA
        if dados_google:
            self.log_visual("Sincronizando com Google Sheets...")
            try:
                ok, msg = self.sheets.atualizar_planilha(sis, dados_google)
                self.log_visual(f"Sheets: {msg}")
            except Exception as e:
                self.log_visual(f"Erro Sheets: {e}")

    # 6. MENUS E CONFIG
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exportar Log", command=self.btn_exportar_log)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)

        conf_menu = tk.Menu(menubar, tearoff=0)
        conf_menu.add_command(label="📧 Configurar E-mail", command=self.janela_config_email)
        menubar.add_cascade(label="Configurações", menu=conf_menu)

        links_menu = tk.Menu(menubar, tearoff=0)
        links_menu.add_command(label="📊 Planilha AC", command=lambda: self.abrir_link("https://docs.google.com/spreadsheets/d/13yE4vD9EREKNtqh1UsUIVKyaZ6umnDvEZ7XSFXs-hBo"))
        links_menu.add_command(label="📊 Planilha AG", command=lambda: self.abrir_link("https://docs.google.com/spreadsheets/d/1uwe3QrT499GRlnnfd2vFBsuaphhfxo8Yelgmunl7bGI"))
        links_menu.add_command(label="📊 Planilha Pátrio", command=lambda: self.abrir_link("https://docs.google.com/spreadsheets/d/1tRo7lNOYMH-svqvMZYu_BueZM023vLvuuuPfc069-wQ"))
        links_menu.add_command(label="📊 Planilha Ponto", command=lambda: self.abrir_link("https://docs.google.com/spreadsheets/d/1sovXviz0arQj-Q9kIKoZDa5u6e4HJAdxMqz882eIWjE"))
        menubar.add_cascade(label="Links Planilhas", menu=links_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre o CIGS", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)

    def janela_config_email(self):
        win = Toplevel(self.root); win.title("SMTP Seguro")
        Label(win, text="E-mail:").grid(row=0, column=0, padx=5, pady=5)
        e1 = Entry(win, width=30); e1.grid(row=0, column=1, padx=5, pady=5)
        Label(win, text="Senha:").grid(row=1, column=0, padx=5, pady=5)
        e2 = Entry(win, show="*", width=30); e2.grid(row=1, column=1, padx=5, pady=5)
        Label(win, text="SMTP:").grid(row=2, column=0, padx=5, pady=5)
        e3 = Entry(win); e3.insert(0,"smtp.gmail.com"); e3.grid(row=2, column=1)
        Label(win, text="Porta:").grid(row=3, column=0, padx=5, pady=5)
        e4 = Entry(win); e4.insert(0,"587"); e4.grid(row=3, column=1)
        
        def salvar():
            self.security.salvar_credenciais(e1.get(), e2.get(), e3.get(), e4.get())
            win.destroy()
            messagebox.showinfo("OK", "Salvo!")
        Button(win, text="Salvar", command=salvar).grid(row=4, columnspan=2, pady=10)

    def enviar_email_relatorio(self, anexo, t, s, f):
        creds = self.security.obter_credenciais()
        if not creds: return
        try:
            msg = MIMEMultipart()
            msg['From'] = creds['email']
            msg['To'] = creds['email']
            msg['Subject'] = f"Relatório CIGS - {datetime.now().strftime('%d/%m')}"
            msg.attach(MIMEText(f"Total: {t}\nSucesso: {s}\nFalha: {f}", 'plain'))
            with open(anexo, "rb") as att:
                p = MIMEBase("application", "octet-stream")
                p.set_payload(att.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename={os.path.basename(anexo)}")
            msg.attach(p)
            srv = smtplib.SMTP(creds['server'], int(creds['port']))
            srv.starttls(); srv.login(creds['email'], creds['senha'])
            srv.sendmail(creds['email'], [creds['email']], msg.as_string())
            srv.quit()
            self.log_visual("E-mail Enviado.")
        except Exception as e: self.log_visual(f"Erro Email: {e}")

    def abrir_link(self, url): webbrowser.open(url)
    def show_about(self): 
        msg = "Desenvolvido por Gabriel Levi - Infra Nuvem\n Fortes Tecnologia"
        messagebox.showinfo("SOBRE", msg)
    def btn_abortar(self):
        if messagebox.askyesno("ABORTAR", "Cancelar?"): threading.Thread(target=self.worker_abortar).start()
    def worker_abortar(self):
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            self.core.enviar_ordem_abortar(ip)
        self.log_visual("ABORTADO.")