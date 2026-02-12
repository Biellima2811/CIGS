import tkinter as tk
from tkinter import ttk
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor

# Importações do Matplotlib
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except:
    HAS_PLOT = False

class DashboardPanel(ttk.Frame):
    def __init__(self, parent, db_manager, core_manager):
        super().__init__(parent)
        self.db = db_manager
        self.core = core_manager # Agora temos acesso ao ping!
        self.setup_ui()
        
        # Inicia atualização automática ao abrir
        self.after(1000, self.atualizar_grid_async)

    def setup_ui(self):
        # Layout dividido: Esquerda (Gráficos), Direita (Semáforo)
        self.columnconfigure(0, weight=6) # 60% largura
        self.columnconfigure(1, weight=4) # 40% largura
        self.rowconfigure(0, weight=1)

        # --- ÁREA 1: GRÁFICOS (Histórico) ---
        self.frame_graph = ttk.LabelFrame(self, text="Telemetria da Frota (Histórico)")
        self.frame_graph.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_matplotlib()

        # --- ÁREA 2: SEMÁFORO (Tempo Real) ---
        self.frame_monitor = ttk.LabelFrame(self, text="🚦 Monitoramento em Tempo Real")
        self.frame_monitor.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Botão de Refresh
        f_top = tk.Frame(self.frame_monitor)
        f_top.pack(fill="x", padx=2, pady=2)
        ttk.Button(f_top, text="🔄 Atualizar Status Agora", command=self.atualizar_grid_async).pack(side="right")
        self.lbl_status = ttk.Label(f_top, text="Aguardando...")
        self.lbl_status.pack(side="left")

        # Canvas com Scrollbar para o Grid (caso tenha muitos servidores)
        self.canvas_grid = tk.Canvas(self.frame_monitor, bg="#ecf0f1", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame_monitor, orient="vertical", command=self.canvas_grid.yview)
        self.scroll_frame = tk.Frame(self.canvas_grid, bg="#ecf0f1")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas_grid.configure(scrollregion=self.canvas_grid.bbox("all"))
        )

        self.canvas_grid.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas_grid.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_grid.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def setup_matplotlib(self):
        if not HAS_PLOT:
            ttk.Label(self.frame_graph, text="Instale matplotlib").pack()
            return

        self.fig = Figure(figsize=(5, 5), layout='constrained', dpi=100)
        self.axs = self.fig.subplot_mosaic([
            ["signal"],
            ["status"]
        ])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_plots()

    def update_plots(self):
        """Atualiza os gráficos com base no histórico do BD"""
        if not HAS_PLOT: return
        try:
            # Busca do Banco de Dados (código corrigido 'limite')
            hist = self.db.obter_historico_recente(limite=30)
            
            if not hist:
                t = np.arange(30); latencia = np.zeros(30)
                on=0; off=0
            else:
                t = np.arange(len(hist))
                latencia = np.array([h['latencia_media'] for h in hist])
                on = hist[-1]['online']; off = hist[-1]['offline']

            # Gráfico de Linha
            ax = self.axs['signal']; ax.clear()
            ax.set_title("Latência Média da Rede (ms)")
            ax.plot(t, latencia, color='#2980b9', linewidth=2)
            ax.fill_between(t, latencia, alpha=0.2, color='#2980b9')
            ax.grid(True, alpha=0.3)

            # Gráfico de Pizza
            ax2 = self.axs['status']; ax2.clear()
            ax2.set_title("Disponibilidade Atual")
            total = on + off
            if total > 0:
                ax2.pie([on, off], labels=['ON', 'OFF'], colors=['#27ae60', '#c0392b'], autopct='%1.1f%%', startangle=90)
            
            self.canvas.draw()
        except Exception as e:
            print(f"Erro Plot: {e}")

    # --- LÓGICA DO SEMÁFORO (GRID) ---
    def atualizar_grid_async(self):
        """Dispara a verificação em background"""
        self.lbl_status.config(text="Escaneando frota...", foreground="blue")
        threading.Thread(target=self._worker_grid, daemon=True).start()

    def _worker_grid(self):
        # 1. Pega lista do Banco
        servidores = self.db.listar_servidores() # [{ip, hostname, cliente...}]
        resultados = []

        # 2. Função rápida de check (ping)
        def check_server(srv):
            ip = srv['ip']
            # Usa check simples (ping http)
            res = self.core.checar_status_agente(ip, "SISTEMA") 
            status = "ONLINE" if res.get('status') == "ONLINE" else "OFFLINE"
            # Simula latência se não vier (ou pega do res se implementado)
            latencia = 10 # ms (Placeholder)
            return {**srv, 'status': status, 'latencia': latencia}

        # 3. Executa em paralelo (Muito rápido!)
        with ThreadPoolExecutor(max_workers=20) as executor:
            resultados = list(executor.map(check_server, servidores))

        # 4. Manda desenhar na tela principal
        self.after(0, lambda: self._render_grid(resultados))

    def _render_grid(self, dados):
        # Limpa grid antigo
        for w in self.scroll_frame.winfo_children(): w.destroy()

        self.lbl_status.config(text=f"Atualizado: {len(dados)} servidores", foreground="green")

        # Configurações de Grid
        colunas_max = 3 # Quantos cartões por linha
        row = 0; col = 0

        for srv in dados:
            # Define cor baseada no status
            if srv['status'] == 'ONLINE':
                cor_bg = "#2ecc71" # Verde
                icone = "☁️ ON"
            else:
                cor_bg = "#e74c3c" # Vermelho
                icone = "💀 OFF"

            # Cria o Cartão (Card) do Servidor
            card = tk.Frame(self.scroll_frame, bg="white", bd=2, relief="groove")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            # Faixa colorida de status
            tk.Label(card, text=icone, bg=cor_bg, fg="white", font=("Arial", 10, "bold"), width=8).pack(side="left", fill="y")
            
            # Informações
            info_frame = tk.Frame(card, bg="white")
            info_frame.pack(side="left", fill="both", expand=True, padx=5)
            
            # Cliente (Truncado se for longo)
            cli_nome = srv['cliente'] if len(srv['cliente']) < 15 else srv['cliente'][:12]+"..."
            tk.Label(info_frame, text=cli_nome, bg="white", font=("Arial", 9, "bold"), anchor="w").pack(fill="x")
            
            # Hostname / IP
            tk.Label(info_frame, text=srv['hostname'], bg="white", fg="gray", font=("Arial", 8), anchor="w").pack(fill="x")
            tk.Label(info_frame, text=srv['ip'], bg="white", fg="#2980b9", font=("Consolas", 8), anchor="w").pack(fill="x")

            # Lógica de quebra de linha do grid
            col += 1
            if col >= colunas_max:
                col = 0
                row += 1

        # Atualiza gráficos também
        self.update_plots()