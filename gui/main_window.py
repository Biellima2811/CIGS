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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Imports do Núcleo
from core.network_ops import CIGSCore
from core.sheets_manager import CIGSSheets
from core.security_manager import CIGSSecurity

# Imports dos Painéis
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
        
        self.monitor_active = False 
        self.setup_window()
        self.setup_sidebar_layout() 
        self.setup_menu()
        
        # Inicia Monitoramento
        self.monitor_active = True
        self.monitor_thread()

    def setup_window(self):
        self.root.title("CIGS - Central de Comandos Integrados v2.5 (Master)")
        self.root.geometry("1280x850")
        try: self.root.state('zoomed')
        except: pass
        try: self.root.iconbitmap("assets/CIGS.ico")
        except: pass
        
    def setup_sidebar_layout(self):
        # Container Principal
        self.paned = tk.PanedWindow(self.root, orient="horizontal", sashwidth=5, bg="#2c3e50")
        self.paned.pack(fill="both", expand=True)

        # --- SIDEBAR (Esquerda) ---
        self.frame_sidebar = tk.Frame(self.paned, bg="#2c3e50", width=220)
        self.paned.add(self.frame_sidebar, minsize=200)
        
        tk.Label(self.frame_sidebar, text="C.I.G.S", font=("Impact", 28), fg="#ecf0f1", bg="#2c3e50").pack(pady=(30, 10))
        tk.Label(self.frame_sidebar, text="Comandos Integrados", font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 30))

        btn_style = {"font": ("Segoe UI", 11, "bold"), "bg": "#34495e", "fg": "white", "activebackground": "#2980b9", "activeforeground": "white", "bd": 0, "pady": 12, "cursor": "hand2", "anchor": "w", "padx": 20}
        
        self.btn_infra = tk.Button(self.frame_sidebar, text="📡  INFRAESTRUTURA", command=lambda: self.show_page("infra"), **btn_style)
        self.btn_infra.pack(fill="x", pady=2)
        
        self.btn_dash = tk.Button(self.frame_sidebar, text="📊  DASHBOARD", command=lambda: self.show_page("dash"), **btn_style)
        self.btn_dash.pack(fill="x", pady=2)
        
        self.btn_db = tk.Button(self.frame_sidebar, text="🏥  CLÍNICA BD", command=lambda: self.show_page("db"), **btn_style)
        self.btn_db.pack(fill="x", pady=2)

        # --- CONTEÚDO (Direita) ---
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

        self.pages = {}
        self.infra_panel = InfraPanel(self.container, {
            'rdp': self.rdp_connect, 'deploy': self.btn_deploy_massa,
            'load_ips': self.btn_carregar_padrao, 'load_csv': self.btn_carregar_dedicados
        })
        self.pages["infra"] = self.infra_panel
        self.dash_panel = DashboardPanel(self.container)
        self.pages["dash"] = self.dash_panel
        self.db_panel = DbPanel(self.container, self.btn_check_db)
        self.pages["db"] = self.db_panel

        for p in self.pages.values(): p.grid(row=0, column=0, sticky="nsew")
        self.show_page("infra")

        # 3. Rodapé (Grid)
        self.frame_bot = tk.Frame(self.frame_content)
        self.frame_bot.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.frame_bot.columnconfigure(0, weight=1)
        
        self.txt_log = scrolledtext.ScrolledText(self.frame_bot, height=6, font=("Consolas", 9))
        self.txt_log.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Botões de Ação
        f_act = tk.Frame(self.frame_bot)
        f_act.grid(row=1, column=0, sticky="ew")
        f_act.columnconfigure(0, weight=1)
        
        ttk.Label(f_act, text='© 2026 Gabriel Levi · Fortes Tecnologia').grid(row=0, column=0, sticky="w", padx=5)
        
        tk.Button(f_act, text="📡 Scanear Infra", command=self.btn_scanear).grid(row=0, column=1, padx=5)
        tk.Button(f_act, text="🚀 PREPARAR MISSÃO (Checklist)", command=self.pre_flight_checklist, 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=10).grid(row=0, column=2, padx=5)

    def show_page(self, name):
        self.pages[name].tkraise()
        def_bg = "#34495e"
        self.btn_infra.config(bg=def_bg); self.btn_dash.config(bg=def_bg); self.btn_db.config(bg=def_bg)
        if name == "infra": self.btn_infra.config(bg="#2980b9")
        if name == "dash": self.btn_dash.config(bg="#2980b9")
        if name == "db": self.btn_db.config(bg="#2980b9")
    
    # --- MONITORAMENTO ---
    def monitor_thread(self):
        def run():
            while self.monitor_active:
                try:
                    sel = self.infra_panel.tree.selection()
                    if sel:
                        ip = self.infra_panel.tree.item(sel[0])['values'][0]
                        sis = self.top_panel.get_data()['sistema']
                        res = self.core.checar_status_agente(ip, sis, full=True) 
                        if res.get('status') == 'ONLINE':
                            self.root.after(0, lambda: self.dash_panel.update_live_stats(ip, res))
                except: pass
                time.sleep(3)
        threading.Thread(target=run, daemon=True).start()

    # --- CHECKLIST ---
    def pre_flight_checklist(self):
        sel = self.infra_panel.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Nenhum servidor selecionado.\nSelecione na lista.")
            return
        
        win = Toplevel(self.root); win.title("Checklist"); win.geometry("450x500")
        tk.Label(win, text="Validação Pré-Missão", font=("Arial", 14, "bold")).pack(pady=10)
        lst = tk.Listbox(win, font=("Consolas", 10), bg="#fdfefe")
        lst.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_go = tk.Button(win, text="AUTORIZAR DISPARO", state="disabled", bg="#e74c3c", fg="white",
                           command=lambda: [win.destroy(), threading.Thread(target=self.worker_disparo, args=(sel,)).start()])
        btn_go.pack(pady=15)

        def add(msg, color="black"):
            lst.insert(tk.END, msg); lst.itemconfig(tk.END, fg=color); lst.see(tk.END); win.update()
            time.sleep(0.2)

        def run_check():
            erros = 0
            d = self.top_panel.get_data()
            add(f"1. Alvos: {len(sel)}", "blue")
            
            if not d['url'] and "Rede Local" not in d['tipo']:
                add("❌ Link AWS vazio!", "red"); erros+=1
            else: add("✅ Parâmetros OK", "green")
            
            if "Rede Local" in d['tipo']:
                paths = [os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                         os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")]
                if any(os.path.exists(p) for p in paths): add("✅ Arquivo local OK", "green")
                else: add("❌ Arquivo local 404!", "red"); erros+=1
            
            ip_teste = self.infra_panel.tree.item(sel[0])['values'][0]
            res = self.core.checar_status_agente(ip_teste, d['sistema'])
            if res.get('status') == "ONLINE": add("✅ Conectividade OK", "green")
            else: add("⚠️ Agente Offline/Instável", "orange")

            if erros == 0:
                add("\n>>> PRONTO PARA COMBATE <<<", "green")
                btn_go.config(state="normal", bg="#27ae60")
            else:
                add("\n❌ ABORTAR", "red")

        threading.Thread(target=run_check).start()

    # --- WORKERS ---
    def log_visual(self, msg):
        self.root.after(0, lambda: self.txt_log.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} {msg}\n") or self.txt_log.see(tk.END))

    def btn_carregar_padrao(self):
        path = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if path:
            ips = self.core.carregar_lista_ips(path)
            self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
            for ip in ips: self.infra_panel.tree.insert("", "end", values=(ip, "...", "-", "-"))
            self.log_visual(f"Carregados: {len(ips)}")

    def btn_carregar_dedicados(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            try:
                ips = []
                with open(path, newline='', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f); next(reader, None)
                    for row in reader:
                        if row and len(row)>0 and row[0].count('.')==3:
                            ips.append((row[0].strip(), row[1] if len(row)>1 else "Dedicado"))
                self.infra_panel.tree.delete(*self.infra_panel.tree.get_children())
                for ip, cli in ips:
                    self.infra_panel.tree.insert("", "end", values=(ip, "...", cli, "-"), tags=("DEDICADO",))
                self.log_visual(f"Dedicados: {len(ips)}")
            except Exception as e: messagebox.showerror("Erro CSV", str(e))

    def btn_scanear(self): threading.Thread(target=self.worker_scan).start()
    def worker_scan(self):
        sis = self.top_panel.get_data()['sistema']
        self.log_visual(f">>> SCAN ({sis}) <<<")
        items = self.infra_panel.tree.get_children()
        on=0; off=0; crit=0
        
        h_model = "N/A"
        if os.path.exists("CIGS_Agent.exe"):
            try:
                import hashlib; h = hashlib.md5()
                with open("CIGS_Agent.exe", "rb") as f: h.update(f.read())
                h_model = h.hexdigest()
            except: pass

        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            cli_orig = self.infra_panel.tree.item(item)['values'][2]
            res = self.core.checar_status_agente(ip, sis)
            
            st = res.get('status')
            tag = "OFFLINE"
            if st == "ONLINE":
                st = f"ON ({res.get('version','?')})"
                tag = "ONLINE"; on+=1
                if h_model != "N/A" and res.get('hash') != h_model:
                    tag = "CRITICO"; st = "⚠️ vDIF"; crit+=1
                cli = cli_orig if cli_orig not in ["-","..."] else res.get('clientes','-')
            else:
                off+=1; cli = cli_orig
            
            vals = (ip, st, cli, res.get('msg',''))
            self.root.after(0, lambda i=item, v=vals, t=tag: self.infra_panel.tree.item(i, values=v, tags=(t,)))
        
        self.log_visual(">>> FIM SCAN <<<")
        self.root.after(0, lambda: self.dash_panel.update_stats(len(items), on, off, crit))

    def btn_disparar(self): self.pre_flight_checklist()

    def worker_disparo(self, selecionados):
        d = self.top_panel.get_data()
        local_exe = ""
        if "Rede Local" in d['tipo']:
            paths = [os.path.join(r"C:\CIGS\Servicos", d['sistema'], f"{d['sistema']}.exe"),
                     os.path.join(r"C:\TITAN\Servicos", d['sistema'], f"{d['sistema']}.exe")]
            local_exe = next((p for p in paths if os.path.exists(p)), None)
            modo = "APENAS_EXEC"
        else: modo = "COMPLETO"

        try: db = datetime.strptime(f"{d['data']} {d['hora']}", "%d/%m/%Y %H:%M")
        except: return

        self.log_visual(">>> DISPARO <<<")
        cnt = 0
        for item_id in selecionados:
            item = self.infra_panel.tree.item(item_id)
            ip = item['values'][0]
            if cnt > 0 and cnt % 10 == 0: db += timedelta(minutes=15)
            dt_str = db.strftime("%d/%m/%Y %H:%M")
            
            copia_ok = True
            if modo == "APENAS_EXEC":
                pasta_sis = "Ponto" if d['sistema'] == "PONTO" else d['sistema']
                dest = f"\\\\{ip}\\C$\\Atualiza\\CloudUp\\CloudUpCmd\\{d['sistema']}\\Atualizadores\\{pasta_sis}\\{d['sistema']}.exe"
                self.log_visual(f"-> {ip}: Copiando...")
                try:
                    path_dir = os.path.dirname(dest)
                    subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                    subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, stdout=subprocess.DEVNULL, check=True)
                except:
                    try:
                        self.log_visual(f"-> {ip}: Autenticando...")
                        subprocess.run(f'net use \\\\{ip}\\C$ /user:{d["user"]} {d["pass"]}', shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'mkdir "{path_dir}"', shell=True, stdout=subprocess.DEVNULL)
                        subprocess.run(f'copy /Y "{local_exe}" "{dest}"', shell=True, stdout=subprocess.DEVNULL, check=True)
                        subprocess.run(f'net use \\\\{ip}\\C$ /delete', shell=True, stdout=subprocess.DEVNULL)
                    except: copia_ok = False; msg = "Erro Copy"

            if copia_ok:
                try: nome = os.path.basename(urlparse(d['url']).path) or "up.rar"
                except: nome = "up.rar"
                suc, msg = self.core.enviar_ordem_agendamento(ip, d['url'], nome, dt_str, d['user'], d['pass'], d['sistema'], modo)
            else: suc=False
            
            tag = "SUCESSO" if suc else "OFFLINE"
            self.root.after(0, lambda i=item_id, m=msg, t=tag: self.infra_panel.tree.item(i, values=list(self.infra_panel.tree.item(i)['values'])[:-1] + [m], tags=(t,)))
            cnt += 1
        self.log_visual(">>> FIM DISPARO <<<")

    def rdp_connect(self, ip):
        d = self.top_panel.get_data()
        try:
            subprocess.run(f'cmdkey /generic:TERMSRV/{ip} /user:"{d["user"]}" /pass:"{d["pass"]}"', shell=True)
            subprocess.Popen(f'mstsc /v:{ip} /admin', shell=True)
        except Exception as e: messagebox.showerror("Erro RDP", str(e))

    def btn_check_db(self): threading.Thread(target=self.worker_db_check).start()
    def worker_db_check(self):
        self.root.after(0, lambda: self.db_panel.clear() or self.db_panel.log("=== CHECK DB ==="))
        sis = self.top_panel.get_data()['sistema']
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            if "OFFLINE" not in self.infra_panel.tree.item(item)['values'][1]:
                self.root.after(0, lambda i=ip: self.db_panel.log(f"Check {i}..."))
                r = self.core.verificar_banco(ip, sis)
                icon = "✅" if "OK" in r.get('status','') else "❌"
                self.root.after(0, lambda t=f"{icon} {r.get('status')}\n{r.get('log')}\n---": self.db_panel.log(t))

    def btn_deploy_massa(self):
        if not messagebox.askyesno("ATENÇÃO", "Deploy do Agente para TODOS?"): return
        threading.Thread(target=self.worker_deploy).start()

    def worker_deploy(self):
        # Esta é a função que faltava no seu código anterior!
        if os.path.exists("CIGS_Agent.dist"): m="PASTA"; o="CIGS_Agent.dist"
        elif os.path.exists("CIGS_Agent.exe"): m="ARQUIVO"; o="CIGS_Agent.exe"
        else: self.log_visual("Falta Agente"); return
        if not os.path.exists("nssm.exe"): self.log_visual("Falta nssm"); return

        self.log_visual(f">>> DEPLOY ({m}) <<<")
        for item in self.infra_panel.tree.get_children():
            ip = self.infra_panel.tree.item(item)['values'][0]
            dest = f"\\\\{ip}\\C$\\CIGS"
            try:
                subprocess.run(f'sc \\\\{ip} stop TITAN_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} delete TITAN_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'sc \\\\{ip} stop CIGS_Service', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /IM TITAN_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'taskkill /S {ip} /IM CIGS_Agent.exe /F', shell=True, stdout=subprocess.DEVNULL)
                time.sleep(2)
                subprocess.run(f'mkdir "{dest}"', shell=True, stdout=subprocess.DEVNULL)
                
                if m=="PASTA": subprocess.run(f'xcopy "{o}" "{dest}" /E /I /Y', shell=True, stdout=subprocess.DEVNULL)
                else: subprocess.run(f'copy /Y "{o}" "{dest}\\CIGS_Agent.exe"', shell=True, stdout=subprocess.DEVNULL)
                
                subprocess.run(f'copy /Y "nssm.exe" "{dest}\\nssm.exe"', shell=True, stdout=subprocess.DEVNULL)
                subprocess.run(f'copy /Y "UnRAR.exe" "{dest}\\UnRAR.exe"', shell=True, stdout=subprocess.DEVNULL)
                
                rmt = r"C:\CIGS\CIGS_Agent.exe"
                subprocess.run(f'wmic /node:"{ip}" process call create "C:\\CIGS\\nssm.exe install CIGS_Service \"{rmt}\""', shell=True, stdout=subprocess.DEVNULL)
                time.sleep(1)
                subprocess.run(f'wmic /node:"{ip}" process call create "C:\\CIGS\\nssm.exe set CIGS_Service AppDirectory \"C:\\CIGS\""', shell=True, stdout=subprocess.DEVNULL)
                
                if subprocess.run(f'sc \\\\{ip} start CIGS_Service', shell=True, stdout=subprocess.DEVNULL).returncode != 0:
                     subprocess.run(f'wmic /node:"{ip}" process call create "{rmt}"', shell=True, stdout=subprocess.DEVNULL)
                self.log_visual(f"-> {ip}: OK")
            except Exception as e: self.log_visual(f"-> {ip}: Falha {e}")
        self.log_visual(">>> FIM DEPLOY <<<")

    def btn_relatorio_final(self):
        if messagebox.askyesno("Relatório", "Gerar?"): threading.Thread(target=self.worker_relatorio).start()
    
    def worker_relatorio(self):
        data = self.top_panel.get_data(); sis = data['sistema']
        dt = datetime.strptime(data['data'], "%d/%m/%Y").strftime("%Y%m%d")
        self.log_visual(">>> RELATÓRIO <<<")
        csv_d = []; t_g=0; s_g=0
        
        items = self.infra_panel.tree.get_children()
        for item in items:
            ip = self.infra_panel.tree.item(item)['values'][0]
            if "OFFLINE" not in self.infra_panel.tree.item(item)['values'][1]:
                res = self.core.obter_relatorio_agente(ip, sis, dt)
                if "erro" not in res:
                    t=res.get('total',0); s=res.get('sucessos',0); p=res.get('porcentagem',0)
                    t_g+=t; s_g+=s; csv_d.append([ip, sis, t, s, f"{p}%", res.get('arquivo')])
                    self.root.after(0, lambda i=item, m=f"Log: {s}/{t}": self.infra_panel.tree.item(i, values=list(self.infra_panel.tree.item(i)['values'])[:-1]+[m]))
        try:
            nome = f"Rel_{sis}_{datetime.now().strftime('%H%M')}.csv"
            with open(nome, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';'); w.writerow(["IP","Sis","Tot","Suc","%","Arq"]); w.writerows(csv_d)
            self.log_visual(f"Salvo: {nome}")
            if csv_d: self.enviar_email_relatorio(nome, t_g, s_g, t_g-s_g)
        except: pass
        
        # Sincronia Google Sheets
        if csv_d:
            try:
                dados_sheets = [[r[0], r[2], r[3], r[4], r[5]] for r in csv_d] # IP, Tot, Suc, %, Arq
                self.sheets.atualizar_planilha(sis, dados_sheets)
                self.log_visual("Planilha Google Atualizada.")
            except: pass

    def btn_exportar_log(self):
        try:
            with open("cigs_log.txt", "w") as f: f.write(self.txt_log.get("1.0", tk.END))
            messagebox.showinfo("OK", "Log Salvo")
        except: pass
    def btn_abortar(self):
        if messagebox.askyesno("STOP", "Cancelar?"): threading.Thread(target=self.worker_abortar).start()
    def worker_abortar(self):
        for item in self.infra_panel.tree.get_children(): self.core.enviar_ordem_abortar(self.infra_panel.tree.item(item)['values'][0])
        self.log_visual("ABORTADO.")
    
    def setup_menu(self):
        menubar = tk.Menu(self.root); self.root.config(menu=menubar)
        f = tk.Menu(menubar, tearoff=0); f.add_command(label="Sair", command=self.root.quit); menubar.add_cascade(label="Arquivo", menu=f)
        c = tk.Menu(menubar, tearoff=0); c.add_command(label="Email", command=self.janela_config_email); menubar.add_cascade(label="Config", menu=c)
        h = tk.Menu(menubar, tearoff=0); h.add_command(label="Sobre", command=self.show_about); menubar.add_cascade(label="Ajuda", menu=h)

    def janela_config_email(self):
        win = Toplevel(self.root); win.title("Email")
        Label(win, text="Email:").grid(row=0,column=0); e1=Entry(win); e1.grid(row=0,column=1)
        Label(win, text="Senha:").grid(row=1,column=0); e2=Entry(win, show="*"); e2.grid(row=1,column=1)
        Button(win, text="Salvar", command=lambda:[self.security.salvar_credenciais(e1.get(),e2.get()), win.destroy()]).grid(row=2,columnspan=2)

    def enviar_email_relatorio(self, anexo, t, s, f):
        c = self.security.obter_credenciais()
        if not c: return
        try:
            msg = MIMEMultipart(); msg['Subject'] = f"Relatorio CIGS {datetime.now().strftime('%d/%m')}"; msg['From'] = c['email']; msg['To'] = c['email']
            with open(anexo, "rb") as a: p=MIMEBase("application","octet-stream"); p.set_payload(a.read()); encoders.encode_base64(p); p.add_header('Content-Disposition',f"attachment; filename={anexo}"); msg.attach(p)
            s = smtplib.SMTP(c['server'], int(c['port'])); s.starttls(); s.login(c['email'], c['senha']); s.sendmail(c['email'], [c['email']], msg.as_string()); s.quit()
            self.log_visual("Email Enviado.")
        except: pass
    
    def abrir_link(self, u): webbrowser.open(u)
    def show_about(self): messagebox.showinfo("CIGS", "v2.5 Master")