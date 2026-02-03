# Importa módulos do Python para manipulação de arquivos, processos, downloads etc.
import os
import sys
import requests
import subprocess
import glob
import shutil
from datetime import datetime

# Importa configurações e caminhos principais do sistema
from .config import PASTA_BASE, PASTA_DOWNLOAD, UNRAR_PATH, MAPA_RAIZ, get_caminho_atualizador

# Importa utilidades (log e permissões)
from .utils import log_debug, ajustar_permissoes

def sanitizar_extracao(destino):
    """
    Função de Limpeza: detecta quando um .rar foi extraído com uma pasta raiz desnecessária
    e move os arquivos para a pasta correta, removendo a pasta extra.
    """
    log_debug(f"Iniciando sanitizacao em: {destino}")
    try:
        # Verifica se o destino existe
        if not os.path.exists(destino): 
            log_debug("Pasta destino nao existe.")
            return

        # Lista todos os itens dentro do destino
        itens = os.listdir(destino)

        # Caso exista apenas 1 item e ele seja uma pasta, é provável que seja uma pasta aninhada
        if len(itens) == 1:
            pasta_intruso = os.path.join(destino, itens[0])

            # Verifica se este item único é uma pasta
            if os.path.isdir(pasta_intruso):
                log_debug(f"Pasta aninhada detectada: {itens[0]}. Movendo arquivos para cima...")
                
                # Move os arquivos da pasta interna para a pasta destino
                for item in os.listdir(pasta_intruso):
                    origem = os.path.join(pasta_intruso, item)
                    dest = os.path.join(destino, item)
                    shutil.move(origem, dest)
                
                # Remove a pasta vazia após mover os arquivos
                os.rmdir(pasta_intruso)
                log_debug("Estrutura corrigida com sucesso.")

        else:
            # Se houver mais itens, assume que a estrutura está correta
            log_debug(f"Estrutura parece correta ou mista ({len(itens)} itens).")
            
    except Exception as e:
        # Loga qualquer falha que ocorrer durante o processo
        log_debug(f"Erro na sanitizacao: {e}")

def agendar_tarefa_universal(url, nome_arquivo, data_hora, usuario, senha, start_in, sistema, modo, script_nome="Executa.bat", script_args=""):
    # Log inicial da missão contendo sistema, script e argumentos enviados pela central
    log_debug(f"--- Missao: {sistema} | Script: {script_nome} | Args: {script_args} ---")

    # Ajusta permissões antes de executar ou criar arquivos
    ajustar_permissoes()
    
    # Determina pasta onde os arquivos devem ser extraídos ou onde o script será executado
    pasta_destino = start_in if start_in else get_caminho_atualizador(sistema)

    # Se não houver caminho válido, retorna erro
    if not pasta_destino: return False, "Caminho invalido"

    # Cria a pasta caso ela não exista
    if not os.path.exists(pasta_destino): 
        try: os.makedirs(pasta_destino)
        except: pass

    # =========================
    # 1. DOWNLOAD DO ARQUIVO
    # =========================
    caminho_arq = os.path.join(PASTA_DOWNLOAD, nome_arquivo)

    if modo == "COMPLETO":
        # Garante que a pasta de downloads exista
        if not os.path.exists(PASTA_DOWNLOAD): os.makedirs(PASTA_DOWNLOAD)

        try:
            # Faz requisição GET para baixar o arquivo
            r = requests.get(url, stream=True, timeout=300)

            if r.status_code == 200:
                # Salva o arquivo em modo binário
                with open(caminho_arq, 'wb') as f:
                    for c in r.iter_content(8192):
                        f.write(c)
            else:
                # Caso o servidor retorne erro HTTP
                return False, f"HTTP {r.status_code}"

        except Exception as e:
            # Em caso de erro na transferência
            return False, f"Download: {e}"
    
    # ======================================
    # 2. GERAR ARQUIVO BAT DINÂMICO
    # ======================================

    # Caminho do arquivo BAT que será gerado e executado pelo agendador
    bat_path = os.path.join(PASTA_BASE, f"Launcher_{sistema}.bat")

    # Caminho para log temporário do processo
    log_bat = r"%TEMP%\cigs_exec.log"

    # Caminho raiz do sistema que vai executar o script
    raiz_sis = MAPA_RAIZ.get(sistema.upper())
    
    # Caminho completo do script que será chamado (Executa.bat, ExecutaOnDemand.bat, etc.)
    target_bat = os.path.join(raiz_sis, script_nome)
    
    cmd_extrai = ""
    cmd_sanitize = ""

    # Caso seja um .rar e modo COMPLETO, monta comandos de extração e sanitização
    if modo == "COMPLETO" and nome_arquivo.lower().endswith(".rar"):
        cmd_extrai = f'"{UNRAR_PATH}" x -y -o+ "{caminho_arq}" "{pasta_destino}\\" >> "{log_bat}"\n'

        # Executável do agente Python em execução
        agente_exe = sys.executable

        # Linha para sanitizar (executa agente com flag --sanitize)
        cmd_sanitize = f'"{agente_exe}" --sanitize "{pasta_destino}" >> "{log_bat}"\n'

    # Comando final que chama o script desejado passando argumentos definidos pela central
    comando_final = f'call "{target_bat}" {script_args} >> "{log_bat}"'

    # Conteúdo completo do BAT gerado dinamicamente
    conteudo_bat = f"""@echo off
echo [%date% %time%] Inicio >> "{log_bat}"
{cmd_extrai}
{cmd_sanitize}
if exist "{target_bat}" (
    cd /d "{raiz_sis}"
    {comando_final}
) else (
    echo ERRO: Script {script_nome} nao encontrado em {raiz_sis} >> "{log_bat}"
)
exit
"""
    try:
        # Cria o arquivo BAT no disco
        with open(bat_path, 'w') as f:
            f.write(conteudo_bat)
    except:
        # Caso haja erro ao gravar o arquivo BAT
        return False, "Erro criar BAT"

    # ======================================
    # 3. AGENDAR TAREFA NO SISTEMA
    # ======================================

    try:
        # Divide data e hora enviadas pela central
        d, h = data_hora.split(" ")
        
        # Sufixo para nome de tarefa baseado no modo de operação
        sufixo = "Full" if modo == "COMPLETO" else "EXE"

        # Nome padrão da tarefa no Windows Task Scheduler
        task_name = f"CIGS_Atualizacao_{sufixo}_{sistema.upper()}"
        
        # Comando para criar tarefa com credenciais do usuário informado
        cmd_sch = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONCE /sd {d} /st {h} /ru "{usuario}" /rp "{senha}" /rl HIGHEST /f'
        
        # Executa comando para criar tarefa
        res = subprocess.run(cmd_sch, shell=True, capture_output=True, text=True)

        # Se criar com sucesso, retorna OK
        if res.returncode == 0:
            return True, f"Agendado: {task_name}"
        
        # Caso falhe, tenta criar como SYSTEM (usuário com mais poderes)
        cmd_sys = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONCE /sd {d} /st {h} /ru SYSTEM /rl HIGHEST /f'
        
        # Se funcionar como SYSTEM, retorna OK
        if subprocess.run(cmd_sys, shell=True).returncode == 0:
            return True, f"Agendado SYSTEM: {task_name}"
        
        # Caso nenhum dos dois consiga, retorna erro
        return False, f"Falha Task: {res.stderr}"

    except Exception as e:
        return False, str(e)


def analisar_log_backup(sistema, data_alvo=None):
    # Obtém pasta raiz do sistema
    path = MAPA_RAIZ.get(sistema.upper())

    if not path:
        return {"erro": "404"}
    
    # Monta o padrão de busca do arquivo StatusBackup_dd-MM-yyyy.txt
    padrao = os.path.join(path, f"StatusBackup_{data_alvo if data_alvo else '*'}.txt")

    # Procura arquivos que batem com o padrão
    logs = glob.glob(padrao)

    # Se não houver logs, retorna mensagem
    if not logs:
        return {"erro": "Sem Logs"}
    
    # Seleciona o arquivo mais recente baseado na data de criação
    log = max(logs, key=os.path.getctime)

    t = 0  # total de updates detectados
    s = 0  # total de sucessos

    try:
        # Abre o log para leitura
        with open(log, 'r', encoding='latin-1') as f:
            for l in f:
                if "Update '" in l:
                    t += 1
                if "Success" in l:
                    s += 1
        
        # Retorna dados de estatística
        return {
            "arquivo": os.path.basename(log),
            "total": t,
            "sucessos": s,
            "porcentagem": round((s/t*100) if t else 0, 1)
        }
    except:
        return {"erro": "Erro Leitura"}

def cancelar_missao():
    try:
        # Deleta qualquer tarefa do agendador cujo nome começa com CIGS
        subprocess.run('schtasks /delete /tn "CIGS*" /f', shell=True)
        return "OK"
    except:
        return "Erro"
