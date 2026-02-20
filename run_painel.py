import os
import sys
import streamlit.web.cli as stcli
import traceback
from datetime import datetime

# Define onde o log será salvo (na mesma pasta do .exe)
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

log_file = os.path.join(base_dir, "dashboard_error.log")

# Função para capturar erros não tratados
def log_exception(exc_type, exc_value, exc_traceback):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- Erro em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ---\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback) # Mantém o comportamento padrão

sys.excepthook = log_exception

if __name__ == "__main__":
    try:
        if getattr(sys, 'frozen', False):
            pasta_atual = sys._MEIPASS # Pasta temporária do PyInstaller
        else:
            pasta_atual = os.path.dirname(os.path.abspath(__file__))
            
        # Aponta para o seu arquivo do dashboard
        script_path = os.path.join(pasta_atual, "painel_gestor.py")
        
        # Configura os argumentos do Streamlit
        sys.argv = [
            "streamlit", 
            "run", script_path, 
            "--server.port=8501", 
            "--server.headless=true", 
            "--global.developmentMode=false"
        ]
        
        sys.exit(stcli.main())
        
    except Exception as e:
        # Captura qualquer erro fatal na hora de iniciar
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- Erro Fatal em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ---\n")
            traceback.print_exc(file=f)
        sys.exit(1)