"""
Arquivo principal de entrada para o Agente CIGS (cigs_core)
Este arquivo define os modos de operação do agente: servidor API ou ferramenta CLI
"""

# Importa o módulo sys para manipulação de argumentos da linha de comando
import sys

# Importa função para iniciar o servidor API do módulo cigs_core.api
from cigs_core.api import iniciar_servidor

# Importa função para sanitização de arquivos extraídos do módulo cigs_core.tasks
from cigs_core.tasks import sanitizar_extracao

# Bloco padrão de execução principal em Python
if __name__ == '__main__':
    # Verifica se foram passados argumentos na linha de comando
    # Se houver mais de 2 argumentos E o primeiro argumento for '--sanitize'
    if len(sys.argv) > 2 and sys.argv[1] == '--sanitize':
        """
        Modo Limpeza (Ferramenta de Linha de Comando - CLI):
        Executado automaticamente pelo script BAT após o processo de descompactação UnRAR
        
        Uso típico: python cigs_agent.py --sanitize "caminho/da/pasta"
        
        Este modo é acionado pelo fluxo de atualização para limpar e organizar
        arquivos extraídos, remover arquivos desnecessários e garantir a 
        integridade da estrutura de diretórios após descompactação.
        """
        
        # O segundo argumento contém o caminho para a pasta a ser sanitizada
        caminho_alvo = sys.argv[2]
        
        # Chama a função de sanitização passando o caminho como parâmetro
        sanitizar_extracao(caminho_alvo)
        
    else:
        """
        Modo Servidor (Padrão):
        Inicia o servidor API REST que escuta por comandos da central CIGS
        
        Uso típico: python cigs_agent.py
        
        Este é o modo de operação normal do agente, onde ele fica aguardando
        requisições HTTP da aplicação principal para executar operações como:
        - Verificação de status
        - Agendamento de atualizações
        - Verificação de banco de dados
        - Coleta de relatórios
        """
        
        # Inicia o servidor web/API na porta configurada (geralmente 5000 ou 8080)
        iniciar_servidor()

# Fluxo de Execução:
# -----------------
# 1. Modo Servidor (Padrão):
#    - O agente é instalado como serviço Windows
#    - Inicia automaticamente na inicialização do sistema
#    - Fica escutando na porta configurada por comandos da central
#
# 2. Modo Limpeza (CLI):
#    - Acionado pelo script BAT após descompactação de atualizações
#    - Processa arquivos extraídos, removendo:
#        * Arquivos temporários (.tmp, .temp)
#        * Logs antigos desnecessários
#        * Arquivos de instalação redundantes
#        * Scripts de configuração obsoletos
#    - Garante que apenas os arquivos essenciais permaneçam
#    - Organiza a estrutura de diretórios conforme padrão do sistema
#
# Contexto de Uso:
# ---------------
# Este arquivo é tipicamente o ponto de entrada do agente CIGS_Agent.exe
# que é distribuído e executado nos servidores clientes. Ele permite que
# o mesmo executivo opere em dois modos distintos baseado na necessidade.