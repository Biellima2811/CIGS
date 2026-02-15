# Importa o módulo os, usado para manipulação de caminhos e verificações no sistema operacional
import os

# Define a porta onde o agente CIGS irá rodar
PORTA = 5580

# Define a versão atual do agente, usada para identificação e diagnóstico
VERSAO_AGENTE = "v3.1 (Multi-System Fix)"

# ================================
#      Caminhos Base do Sistema
# ================================

# Diretório principal onde o agente armazena seus dados
PASTA_BASE = r'C:\CIGS'

# Diretório onde serão armazenados downloads realizados pelo agente
PASTA_DOWNLOAD = os.path.join(PASTA_BASE, "Downloads")

# Caminho completo do arquivo de log de debug
ARQUIVO_LOG_DEBUG = os.path.join(PASTA_BASE, "CIGS_debug.log")

# Caminho do executável UnRAR usado para extrair arquivos .rar
UNRAR_PATH = os.path.join(PASTA_BASE, "UnRAR.exe")

# ======================================
#   Detecção Automática do Firebird
# ======================================

# Caminho padrão do isql.exe do Firebird 2.5
ISQL_PATH = r"C:\Program Files\Firebird\Firebird_2_5\bin\isql.exe"

# Caso o caminho oficial não exista, tenta o caminho usado por instalações da Fortes
if not os.path.exists(ISQL_PATH):
    ISQL_PATH = r"C:\Fortes\Firebird_5_0\isql.exe"

# ==========================================================
#   Mapeamento das Raízes onde ficam os scripts Executa.bat
# ==========================================================

MAPA_RAIZ = {
    # Atualizador do sistema AC
    "AC": r"C:\Atualiza\CloudUp\CloudUpCmd\AC",

    # Atualizador do sistema AG
    "AG": r"C:\Atualiza\CloudUp\CloudUpCmd\AG",

    # Atualizador do sistema Ponto
    "PONTO": r"C:\Atualiza\CloudUp\CloudUpCmd\PONTO",

    # Atualizador do sistema Patrio
    "PATRIO": r"C:\Atualiza\CloudUp\CloudUpCmd\PATRIO"
}

def get_caminho_atualizador(sistema):
    """
    Retorna o caminho da pasta de instalação (onde os pacotes são extraídos).
    Exemplo: C:\Atualiza\CloudUp\CloudUpCmd\AC\Atualizadores\AC
    """
    raiz = MAPA_RAIZ.get(sistema.upper())
    if not raiz:
        return None
    # O nome da subpasta é o mesmo da última parte da raiz, mas com a capitalização correta
    # Se necessário, use um mapa específico para os nomes das pastas
    if sistema.upper() == "PONTO":
        subpasta = "Ponto"
    elif sistema.upper() == "PATRIO":
        subpasta = "Patrio"
    else:
        subpasta = sistema.upper()
    return os.path.join(raiz, "Atualizadores", subpasta)