# Importa o módulo principal do Tkinter para criar interfaces gráficas
import tkinter as tk
# Importa ttk (themed widgets) e scrolledtext (caixa de texto com barra de rolagem)
from tkinter import ttk, scrolledtext

# Classe que representa o painel de ferramentas de banco de dados
class DbPanel(ttk.Frame):
    def __init__(self, parent, check_callback):
        # Inicializa a classe base (Frame) dentro do container "parent"
        super().__init__(parent)
        # Função que será chamada quando o botão de "Check-up" for clicado
        self.on_check = check_callback
        # Monta a interface gráfica
        self.setup_ui()

    def setup_ui(self):
        # Configura a coluna principal para expandir proporcionalmente
        self.columnconfigure(0, weight=1)
        # Configura a linha 1 (área de log) para expandir
        self.rowconfigure(1, weight=1)
        
        # Barra de Ferramentas (parte superior)
        top = ttk.Frame(self, padding=10)
        # Posiciona a barra na linha 0, coluna 0, expandindo horizontalmente
        top.grid(row=0, column=0, sticky="ew")
        
        # Label informativo na barra de ferramentas
        ttk.Label(top, text="Ferramentas de Banco (Firebird/SQL)").pack(side="left")
        
        # Botões de Ação
        # Botão para executar o check-up de integridade do banco
        ttk.Button(top, text="🩺 1. Executar Check-up (Integridade)", command=self.on_check).pack(side="right", padx=5)
        # Botão de limpeza (Sweep), desabilitado por enquanto
        ttk.Button(top, text="🧹 2. Limpeza (Sweep - Breve)", state="disabled").pack(side="right", padx=5)

        # Área de Log (parte inferior)
        # Caixa de texto com barra de rolagem para mostrar logs
        self.log_area = scrolledtext.ScrolledText(self, height=20, font=("Consolas", 9))
        # Posiciona a área de log na linha 1, coluna 0, expandindo em todas direções
        self.log_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def log(self, text):
        # Insere uma nova linha de texto no final da área de log
        self.log_area.insert(tk.END, text + "\n")
        # Faz a rolagem automática para mostrar sempre a última linha
        self.log_area.see(tk.END)
    
    def clear(self):
        # Limpa todo o conteúdo da área de log
        self.log_area.delete(1.0, tk.END)
