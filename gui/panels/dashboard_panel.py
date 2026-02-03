# Importa o módulo principal do Tkinter para criar interfaces gráficas
import tkinter as tk
# Importa o módulo ttk (themed widgets) para usar componentes visuais mais modernos
from tkinter import ttk

# Tenta importar os módulos necessários para integrar gráficos do matplotlib dentro do Tkinter
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Permite renderizar gráficos no Tkinter
    from matplotlib.figure import Figure  # Classe para criar figuras/gráficos
    HAS_PLOT = True  # Flag indicando que matplotlib está disponível
except:
    HAS_PLOT = False  # Caso matplotlib não esteja instalado, define como False

# Classe que representa o painel principal do Dashboard
class DashboardPanel(ttk.Frame):
    def __init__(self, parent):
        # Inicializa a classe base (Frame) dentro do container "parent"
        super().__init__(parent)
        # Chama o método que monta a interface gráfica
        self.setup_ui()

    def setup_ui(self):
        # Configura a coluna principal para expandir proporcionalmente
        self.columnconfigure(0, weight=1)
        # Linha 0 terá peso (gráfico ocupa espaço flexível)
        self.rowconfigure(0, weight=1) # Gráfico
        # Linha 1 terá peso fixo (informações no rodapé)
        self.rowconfigure(1, weight=0) # Info

        # 1. Frame para o gráfico
        self.frame_graph = ttk.LabelFrame(self, text="Status Global da Frota")
        # Posiciona o frame na linha 0, coluna 0, expandindo em todas direções
        self.frame_graph.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Se matplotlib não estiver disponível, mostra aviso
        if not HAS_PLOT:
            ttk.Label(self.frame_graph, text="Instale matplotlib", font=("Arial", 14)).pack(expand=True)
        else:
            # Caso matplotlib esteja disponível, mostra status inicial
            self.lbl_status = ttk.Label(self.frame_graph, text="Aguardando Scan...", font=("Arial", 12))
            self.lbl_status.pack(pady=20)

        # 2. Frame para monitoramento em tempo real (rodapé do dashboard)
        self.frame_live = ttk.LabelFrame(self, text="Monitoramento em Tempo Real (Selecione um servidor na lista)")
        self.frame_live.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Labels para exibir informações do servidor selecionado
        self.lbl_ip = ttk.Label(self.frame_live, text="IP: -", font=("Consolas", 12, "bold"))
        self.lbl_ip.grid(row=0, column=0, padx=20, pady=10)
        
        self.lbl_ram = ttk.Label(self.frame_live, text="RAM: -", font=("Arial", 11))
        self.lbl_ram.grid(row=0, column=1, padx=20)
        
        self.lbl_disk = ttk.Label(self.frame_live, text="Disco Livre: -", font=("Arial", 11))
        self.lbl_disk.grid(row=0, column=2, padx=20)
        
        self.lbl_ver = ttk.Label(self.frame_live, text="Versão: -", font=("Arial", 11))
        self.lbl_ver.grid(row=0, column=3, padx=20)

    def update_stats(self, total, on, off, crit):
        # Atualiza o gráfico com os dados recebidos
        if not HAS_PLOT: return  # Se não houver matplotlib, não faz nada
        # Remove widgets anteriores do frame do gráfico
        for w in self.frame_graph.winfo_children(): w.destroy()
        
        # Se não houver dados, mostra mensagem
        if total == 0: 
            ttk.Label(self.frame_graph, text="Sem dados.", font=("Arial", 12)).pack(pady=20)
            return

        # Cria layout lado a lado (gráfico à esquerda, texto à direita)
        f_left = ttk.Frame(self.frame_graph); f_left.pack(side="left", fill="both", expand=True)
        f_right = ttk.Frame(self.frame_graph); f_right.pack(side="right", fill="y", padx=20)

        # Cria figura do gráfico
        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)  # Adiciona eixo
        # Cria gráfico de barras horizontais com os dados
        ax.barh(['Online', 'Offline', 'Crítico'], [on, off, crit], color=['#2ecc71', '#e74c3c', '#f1c40f'])
        ax.set_title(f"Total: {total}")  # Define título com total de servidores
        
        # Renderiza o gráfico dentro do frame esquerdo
        canv = FigureCanvasTkAgg(fig, master=f_left)
        canv.draw()
        canv.get_tk_widget().pack(fill="both", expand=True)
        
        # Exibe texto com resumo dos dados à direita
        ttk.Label(f_right, text=f"ON: {on}\nOFF: {off}", font=("Arial", 14, "bold")).pack(pady=40)

    def update_live_stats(self, ip, dados):
        # Atualiza os labels inferiores com informações do servidor selecionado
        self.lbl_ip.config(text=f"IP: {ip}")
        self.lbl_ver.config(text=f"Ver: {dados.get('version','?')}")
        
        # Obtém valores de RAM e Disco do dicionário "dados"
        ram = dados.get('ram', 0)
        disk = dados.get('disk', 0)
        
        # Atualiza RAM, mudando cor para vermelho se uso > 90%
        self.lbl_ram.config(text=f"RAM: {ram}%", foreground="red" if ram > 90 else "black")
        # Atualiza Disco, mudando cor para vermelho se espaço < 5 GB
        self.lbl_disk.config(text=f"Disco: {disk} GB", foreground="red" if disk < 5 else "black")
