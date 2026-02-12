import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class DbPanel(ttk.Frame):
    def __init__(self, parent, callback_check, callback_scan, callback_schedule):
        super().__init__(parent)
        self.cb_check = callback_check
        self.cb_scan = callback_scan         # Nova Função de Scan
        self.cb_schedule = callback_schedule # Nova Função de Agendar
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # --- CONTROLES SUPERIORES ---
        f_top = ttk.LabelFrame(self, text="Configuração da Clínica")
        f_top.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        f_top.columnconfigure(1, weight=1)

        ttk.Label(f_top, text="Motor de Banco de Dados:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.var_motor = tk.StringVar(value="FIREBIRD")
        rb_fb = ttk.Radiobutton(f_top, text="🔥 Firebird", variable=self.var_motor, value="FIREBIRD", command=self.toggle_motor)
        rb_ms = ttk.Radiobutton(f_top, text="🗄️ SQL Server (MSSQL)", variable=self.var_motor, value="MSSQL", command=self.toggle_motor)
        rb_fb.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        rb_ms.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        ttk.Label(f_top, text="Nome/Caminho do Banco:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ent_banco = ttk.Entry(f_top, width=40)
        self.ent_banco.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.ent_banco.insert(0, "D:\\BDS\\FORTES_DEMO\\DADOS.FDB")  # Padrão

        # --- ÁREA DE AÇÕES ---
        self.f_actions = ttk.LabelFrame(self, text="Procedimentos Cirúrgicos")
        self.f_actions.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Renderiza os botões iniciais
        self.toggle_motor()

        # --- LOG DE SAÍDA ---
        f_log = ttk.LabelFrame(self, text="Relatório(Log)")
        f_log.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        f_log.rowconfigure(0, weight=1)
        f_log.columnconfigure(0, weight=1)

        self.txt_log = scrolledtext.ScrolledText(f_log, height=10, font=("Consolas", 9))
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        btn_cls = ttk.Button(f_log, text="Limpar Log", command=self.clear)
        btn_cls.grid(row=1, column=0, sticky="e", padx=5, pady=2)

    def toggle_motor(self):
        # Limpa botões antigos
        for widget in self.f_actions.winfo_children():
            widget.destroy()

        motor = self.var_motor.get()

        if motor == "FIREBIRD":
            self.ent_banco.delete(0, tk.END)
            self.ent_banco.insert(0, "C:\\Sistema\\DADOS.FDB")

            btn_opts = [
                ("1. Verificar Integridade (Check)", "CHECK"),
                ("2. Corrigir Erros (Mend)", "MEND"),
                ("3. Limpeza (Sweep)", "SWEEP"),
                ("4. Backup (GBK)", "BACKUP"),
                ("5. Restore (FDB)", "RESTORE"),
                ("⚡ MANUTENÇÃO AUTOMÁTICA (1-5)", "AUTO")
            ]

            for i, (txt, cmd) in enumerate(btn_opts):
                r = i // 3
                c = i % 3
                b = ttk.Button(self.f_actions, text=txt, command=lambda c=cmd: self.cb_check(c, "FIREBIRD"))
                b.grid(row=r, column=c, sticky="ew", padx=5, pady=5, ipady=5)
                self.f_actions.columnconfigure(c, weight=1)

        elif motor == "MSSQL":
            self.ent_banco.delete(0, tk.END)
            self.ent_banco.insert(0, "NOME_DO_BANCO")

            ttk.Label(self.f_actions, text="Scripts T-SQL Avançados:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

            b1 = ttk.Button(self.f_actions, text="🛠️ EXECUTAR MANUTENÇÃO COMPLETA (Script CIGS)",
                            command=lambda: self.cb_check("MAINTENANCE", "MSSQL"))
            b1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=5, ipady=5)

            b2 = ttk.Button(self.f_actions, text="🔍 Apenas CheckDB (Integridade)",
                            command=lambda: self.cb_check("CHECKDB", "MSSQL"))
            b2.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=2)

            ttk.Label(self.f_actions, text="Nota: O script realiza CheckDB, Snapshot Isolation e Reindexação Inteligente.",
                      foreground="gray").grid(row=3, column=0, columnspan=2, pady=5)

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def clear(self):
        self.txt_log.delete("1.0", tk.END)

    def get_db_path(self):
        return self.ent_banco.get().strip()
