# cigs_core/config.py
import os

PORTA = 5578
VERSAO_AGENTE = "v2.0 (Precision Modular)"

# Caminhos Base
PASTA_BASE = r'C:\CIGS'
PASTA_DOWNLOAD = os.path.join(PASTA_BASE, "Downloads")
ARQUIVO_LOG_DEBUG = os.path.join(PASTA_BASE, "CIGS_debug.log")
UNRAR_PATH = os.path.join(PASTA_BASE, "UnRAR.exe")

# Detecção Automática do Firebird
ISQL_PATH = r"C:\Program Files\Firebird\Firebird_2_5\bin\isql.exe"
if not os.path.exists(ISQL_PATH):
    ISQL_PATH = r"C:\Fortes\Firebird_5_0\isql.exe"

# Mapeamento das Raízes (Onde fica o Executa.bat)
MAPA_RAIZ = {
    "AC": r"C:\Atualiza\CloudUp\CloudUpCmd\AC",
    "AG": r"C:\Atualiza\CloudUp\CloudUpCmd\AG",
    "PONTO": r"C:\Atualiza\CloudUp\CloudUpCmd\PONTO",
    "PATRIO": r"C:\Atualiza\CloudUp\CloudUpCmd\PATRIO"
}

def get_caminho_atualizador(sistema):
    """
    Retorna o caminho exato para extração:
    Ex: C:\Atualiza\CloudUp\CloudUpCmd\AC\Atualizadores\AC
    """
    raiz = MAPA_RAIZ.get(sistema.upper())
    if not raiz: return None
    
    # Tratamento para nomes de pasta (PONTO -> Ponto, se necessário)
    subpasta = sistema.upper()
    if sistema.upper() == "PONTO": subpasta = "Ponto"
    
    return os.path.join(raiz, "Atualizadores", subpasta)