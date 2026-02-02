# cigs_core/tasks.py
import os
import requests
import subprocess
import glob
import shutil
from datetime import datetime
from .config import PASTA_BASE, PASTA_DOWNLOAD, UNRAR_PATH, MAPA_RAIZ, get_caminho_atualizador
from .utils import log_debug, ajustar_permissoes

def sanitizar_extracao(destino):
    """
    Função de Limpeza: Tira arquivos de subpastas (ex: AtualizaAC) e joga na raiz.
    """
    log_debug(f"Iniciando sanitizacao em: {destino}")
    try:
        if not os.path.exists(destino): 
            log_debug("Pasta destino nao existe.")
            return

        itens = os.listdir(destino)
        # Se houver apenas 1 item e for uma pasta (Sintoma clássico de extração com pasta raiz)
        if len(itens) == 1:
            pasta_intruso = os.path.join(destino, itens[0])
            if os.path.isdir(pasta_intruso):
                log_debug(f"Pasta aninhada detectada: {itens[0]}. Movendo arquivos para cima...")
                
                # Move cada arquivo da subpasta para a pasta correta
                for item in os.listdir(pasta_intruso):
                    origem = os.path.join(pasta_intruso, item)
                    dest = os.path.join(destino, item)
                    shutil.move(origem, dest)
                
                # Remove a pasta vazia
                os.rmdir(pasta_intruso)
                log_debug("Estrutura corrigida com sucesso.")
        else:
            log_debug(f"Estrutura parece correta ou mista ({len(itens)} itens).")
            
    except Exception as e:
        log_debug(f"Erro na sanitizacao: {e}")

def agendar_tarefa_universal(url, nome_arquivo, data_hora, usuario, senha, start_in, sistema, modo):
    log_debug(f"--- Nova Missao ({modo}): {sistema} ---")
    ajustar_permissoes()
    
    # Define pasta de destino correta (...\Atualizadores\AC)
    # Se start_in vier vazio, calcula. Se vier, usa ele (flexibilidade).
    pasta_destino = start_in if start_in else get_caminho_atualizador(sistema)
    
    if not pasta_destino: return False, "Caminho do sistema não encontrado."
    if not os.path.exists(pasta_destino):
        try: os.makedirs(pasta_destino)
        except: pass

    # 1. Download (Se modo COMPLETO)
    caminho_arq = os.path.join(PASTA_DOWNLOAD, nome_arquivo)
    if modo == "COMPLETO":
        if not os.path.exists(PASTA_DOWNLOAD): os.makedirs(PASTA_DOWNLOAD)
        try:
            r = requests.get(url, stream=True, timeout=300)
            if r.status_code == 200:
                with open(caminho_arq, 'wb') as f:
                    for c in r.iter_content(8192): f.write(c)
            else: return False, f"HTTP {r.status_code}"
        except Exception as e: return False, f"Download: {e}"
    
    # 2. Gerar BAT (Com Correção Automática)
    bat_path = os.path.join(PASTA_BASE, f"Launcher_{sistema}.bat")
    log_bat = r"%TEMP%\cigs_exec.log"
    raiz_sis = MAPA_RAIZ.get(sistema.upper())
    exec_bat = os.path.join(raiz_sis, "Executa.bat")
    
    cmd_extrai = ""
    cmd_sanitize = ""
    
    if modo == "COMPLETO" and nome_arquivo.lower().endswith(".rar"):
        # Extração
        cmd_extrai = f'"{UNRAR_PATH}" x -y -o+ "{caminho_arq}" "{pasta_destino}\\" >> "{log_bat}"\n'

        # Sanitização: Chama o próprio Agente para arrumar a pasta IMEDIATAMENTE após extrair
        agente_exe = sys.executable # Caminho do CIGS_Agent.exe
        cmd_sanitize = f'"{agente_exe}" --sanitize "{pasta_destino}" >> "{log_bat}"\n'

    # Montagem do Script
    conteudo_bat = f"""@echo off
echo [%date% %time%] Inicio Missao >> "{log_bat}"

REM 1. Extrair Arquivos
{cmd_extrai}

REM 2. Corrigir Pastas (Sanitizacao)
{cmd_sanitize}

REM 3. Executar Atualizacao (Executa.bat)
if exist "{exec_bat}" (
    cd /d "{raiz_sis}"
    call "{exec_bat}" >> "{log_bat}"
) else (
    echo ERRO: Executa.bat nao encontrado em {raiz_sis} >> "{log_bat}"
)
exit
"""
    
    conteudo_bat = f"""@echo off
echo [%date% %time%] Inicio >> "{log_bat}"
{cmd_extrai}
if exist "{exec_bat}" (
    cd /d "{raiz_sis}"
    call "{exec_bat}" >> "{log_bat}"
) else (
    echo ERRO: Executa.bat nao achado em {raiz_sis} >> "{log_bat}"
)
exit
"""
    
    try:
        with open(bat_path, 'w') as f: f.write(conteudo_bat)
    except: return False, "Erro ao criar BAT"

    # 3. Agendar
    try:
        d, h = data_hora.split(" ")
        task = f"CIGS_{sistema}_{datetime.now().strftime('%H%M%S')}" # Nome curto
        c = f'schtasks /create /tn "{task}" /tr "{bat_path}" /sc ONCE /sd {d} /st {h} /ru "{usuario}" /rp "{senha}" /rl HIGHEST /f'
        
        res = subprocess.run(c, shell=True, capture_output=True, text=True)
        if res.returncode == 0: 
            return True, f"Agendado {h}"
        
        # Fallback SYSTEM
        c2 = f'schtasks /create /tn "{task}" /tr "{bat_path}" /sc ONCE /sd {d} /st {h} /ru SYSTEM /rl HIGHEST /f'
        if subprocess.run(c2, shell=True).returncode == 0: return True, "Agendado (SYSTEM)"
        
        return False, f"Falha Task: {res.stderr}"
    except Exception as e: return False, str(e)

def analisar_log_backup(sistema, data_alvo=None):
    # Função que estava no seu código original e foi restaurada
    path = MAPA_RAIZ.get(sistema.upper())
    if not path: return {"erro": "404"}
    
    padrao = os.path.join(path, f"StatusBackup_{data_alvo if data_alvo else '*'}.txt")
    logs = glob.glob(padrao)
    if not logs: return {"erro": "Sem Logs"}
    
    log = max(logs, key=os.path.getctime)
    t=0; s=0
    try:
        with open(log, 'r', encoding='latin-1') as f:
            for l in f:
                if "Update '" in l: t+=1
                if "Success" in l: s+=1
        return {"arquivo": os.path.basename(log), "total": t, "sucessos": s, "porcentagem": round((s/t*100) if t else 0, 1)}
    except: return {"erro": "Erro Leitura"}

def cancelar_missao():
    try: subprocess.run('schtasks /delete /tn "CIGS*" /f', shell=True); return "OK"
    except: return "Erro"