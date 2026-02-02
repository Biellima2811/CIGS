import tkinter as tk
from tkinter import ttk
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_PLOT = True
except: HAS_PLOT = False

class DashboardPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1) # Gráfico
        self.rowconfigure(1, weight=0) # Info

        # 1. Gráfico
        self.frame_graph = ttk.LabelFrame(self, text="Status Global da Frota")
        self.frame_graph.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        if not HAS_PLOT:
            ttk.Label(self.frame_graph, text="Instale matplotlib", font=("Arial", 14)).pack(expand=True)
        else:
            self.lbl_status = ttk.Label(self.frame_graph, text="Aguardando Scan...", font=("Arial", 12))
            self.lbl_status.pack(pady=20)

        # 2. Monitor Live (Rodapé do Dashboard)
        self.frame_live = ttk.LabelFrame(self, text="Monitoramento em Tempo Real (Selecione um servidor na lista)")
        self.frame_live.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Grid de Labels
        self.lbl_ip = ttk.Label(self.frame_live, text="IP: -", font=("Consolas", 12, "bold"))
        self.lbl_ip.grid(row=0, column=0, padx=20, pady=10)
        
        self.lbl_ram = ttk.Label(self.frame_live, text="RAM: -", font=("Arial", 11))
        self.lbl_ram.grid(row=0, column=1, padx=20)
        
        self.lbl_disk = ttk.Label(self.frame_live, text="Disco Livre: -", font=("Arial", 11))
        self.lbl_disk.grid(row=0, column=2, padx=20)
        
        self.lbl_ver = ttk.Label(self.frame_live, text="Versão: -", font=("Arial", 11))
        self.lbl_ver.grid(row=0, column=3, padx=20)

    def update_stats(self, total, on, off, crit):
        # Atualiza gráfico
        if not HAS_PLOT: return
        for w in self.frame_graph.winfo_children(): w.destroy()
        
        if total == 0: 
            ttk.Label(self.frame_graph, text="Sem dados.", font=("Arial", 12)).pack(pady=20)
            return

        # Layout Lado a Lado
        f_left = ttk.Frame(self.frame_graph); f_left.pack(side="left", fill="both", expand=True)
        f_right = ttk.Frame(self.frame_graph); f_right.pack(side="right", fill="y", padx=20)

        # Barra Horizontal
        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(['Online', 'Offline', 'Crítico'], [on, off, crit], color=['#2ecc71', '#e74c3c', '#f1c40f'])
        ax.set_title(f"Total: {total}")
        
        canv = FigureCanvasTkAgg(fig, master=f_left)
        canv.draw()
        canv.get_tk_widget().pack(fill="both", expand=True)
        
        # Texto
        ttk.Label(f_right, text=f"ON: {on}\nOFF: {off}", font=("Arial", 14, "bold")).pack(pady=40)

    def update_live_stats(self, ip, dados):
        # Atualiza os labels inferiores
        self.lbl_ip.config(text=f"IP: {ip}")
        self.lbl_ver.config(text=f"Ver: {dados.get('version','?')}")
        
        ram = dados.get('ram', 0)
        disk = dados.get('disk', 0)
        
        self.lbl_ram.config(text=f"RAM: {ram}%", foreground="red" if ram > 90 else "black")
        self.lbl_disk.config(text=f"Disco: {disk} GB", foreground="red" if disk < 5 else "black")