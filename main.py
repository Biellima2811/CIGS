"""
Arquivo principal de entrada da aplicação desktop CIGS
Este é o ponto de inicialização da interface gráfica do usuário (GUI)
"""

# Importa tkinter para criação da interface gráfica
import tkinter as tk

# Importa ThemedTk para janelas com temas modernos pré-definidos
from ttkthemes import ThemedTk

# Importa a classe principal da aplicação CIGS
from gui.main_window import CIGSApp

# Bloco padrão de execução principal em Python
if __name__ == "__main__":
    """
    Ponto de entrada principal da aplicação CIGS Desktop
    Aqui iniciamos a interface gráfica e a janela principal
    """
    
    # Tenta criar uma janela com tema "radiance" do ttkthemes
    try:
        #root = ThemedTk(theme="arc")  # Tema alternativo comentado
        root = ThemedTk(theme="radiance")  # Usa tema "radiance" (claro/azulado)
    except:
        """
        Bloco de fallback: caso ocorra algum erro na criação da janela temática
        Isso pode acontecer se:
        1. A biblioteca ttkthemes não estiver instalada
        2. O tema "radiance" não estiver disponível no sistema
        3. Problemas de compatibilidade com a versão do Tkinter
        
        Nesse caso, usamos a janela padrão do tkinter (sem tema especial)
        """
        root = tk.Tk()  # Cria janela tkinter padrão (fallback)
        root.withdraw() # Esconde a janela cinza vazia
        
    # Instancia a aplicação CIGS passando a janela raiz como parâmetro
    app = CIGSApp(root)
    
    if root.winfo_exists():
        root.deiconify() # Mostra a janela principal agora que carregou
        root.mainloop()

# Fluxo de Execução:
# -----------------
# 1. O script é executado (python main.py ou via executável)
# 2. Verifica se é o módulo principal (__name__ == "__main__")
# 3. Tenta criar janela com tema "radiance" (estilo moderno)
# 4. Se falhar, cria janela tkinter padrão (compatibilidade)
# 5. Instancia a classe CIGSApp, que configura toda a interface
# 6. Inicia o loop de eventos que mantém a aplicação rodando

# Sobre o Tema "radiance":
# -----------------------
# O tema "radiance" é um dos temas incluídos na biblioteca ttkthemes
# Características:
# - Interface clara e moderna
# - Cores azuladas (accent color)
# - Bordas arredondadas e visual limpo
# - Compatível com widgets ttk (themed tk)

# Estrutura de Diretórios Esperada:
# --------------------------------
# projeto/
# │
# ├── main.py              # Este arquivo
# ├── gui/
# │   └── main_window.py   # Classe CIGSApp
# ├── core/                # Módulos de núcleo
# └── assets/              # Recursos visuais (ícones, imagens)

# Requisitos do Sistema:
# ---------------------
# 1. Python 3.6+
# 2. Bibliotecas necessárias:
#    - tkinter (geralmente incluído com Python)
#    - ttkthemes (pip install ttkthemes)
#    - Outras dependências do projeto CIGS

# Modos de Execução Alternativos:
# -----------------------------
# 1. Execução direta: python main.py
# 2. Via executável: (após pyinstaller ou similar)
# 3. Como módulo: python -m gui.main (se configurado)

# Tratamento de Erros:
# -------------------
# O bloco try-except garante que a aplicação inicie mesmo se:
# - O usuário não tiver o ttkthemes instalado
# - Houver problemas com o tema específico
# - Configuração de display incompatível

# Nota sobre Performance:
# ----------------------
# A inicialização com tema pode ser ligeiramente mais lenta
# mas proporciona melhor experiência visual e consistência
# entre diferentes plataformas (Windows/Linux)