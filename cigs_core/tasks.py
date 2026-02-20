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
    # Log inicial
    log_debug(f"--- Missao: {sistema} | Script: {script_nome} ---", sistema)
    
    ajustar_permissoes()
    
    # pasta_destino é onde os arquivos do pacote serão colocados (pasta de instalação, com Atualizadores)
    pasta_destino = start_in if start_in else get_caminho_atualizador(sistema)
    if not pasta_destino:
        return False, "Caminho invalido"

    # Cria a pasta destino se não existir
    if not os.path.exists(pasta_destino):
        try:
            os.makedirs(pasta_destino)
        except:
            pass

    # ====================================================
    # 2. OPERAÇÃO DE DOWNLOAD E EXTRAÇÃO (se modo COMPLETO)
    # ====================================================
    if modo == "COMPLETO":
        if not os.path.exists(PASTA_DOWNLOAD):
            os.makedirs(PASTA_DOWNLOAD)
        caminho_rar = os.path.join(PASTA_DOWNLOAD, nome_arquivo)

        try:
            log_debug("Baixando pacote...", sistema)
            r = requests.get(url, stream=True, timeout=300)
            if r.status_code == 200:
                with open(caminho_rar, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            else:
                return False, f"HTTP Download {r.status_code}"
        except Exception as e:
            return False, f"Erro Download: {e}"

        try:
            temp_extract = os.path.join(PASTA_BASE, "Temp_Install")
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract, ignore_errors=True)
            os.makedirs(temp_extract)

            log_debug("Extraindo para temporario...", sistema)
            subprocess.run(f'"{UNRAR_PATH}" x -y "{caminho_rar}" "{temp_extract}\\"', shell=True, stdout=subprocess.DEVNULL)

            # Lógica de correção de pasta (anti-subpasta)
            items = os.listdir(temp_extract)
            source_folder = temp_extract
            if len(items) == 1 and os.path.isdir(os.path.join(temp_extract, items[0])):
                source_folder = os.path.join(temp_extract, items[0])
                log_debug(f"Subpasta detectada ({items[0]}). Ajustando origem.", sistema)

            log_debug(f"Movendo arquivos para: {pasta_destino}", sistema)
            cmd_copy = f'xcopy "{source_folder}\\*" "{pasta_destino}\\" /E /H /C /I /Y'
            subprocess.run(cmd_copy, shell=True, stdout=subprocess.DEVNULL)

            shutil.rmtree(temp_extract, ignore_errors=True)
            try:
                os.remove(caminho_rar)
            except:
                pass

        except Exception as e:
            log_debug(f"Erro na Instalação: {e}", sistema)
            return False, f"Erro Install: {e}"

    # ======================================
    # 3. GERAR BAT DE EXECUÇÃO
    # ======================================
    # Determina a pasta onde o script .bat está (raiz do sistema)
    if pasta_destino and 'Atualizadores' in pasta_destino:
        # Sobe dois níveis: de ...\Ponto\Atualizadores\Ponto para ...\Ponto
        pasta_scripts = os.path.dirname(os.path.dirname(pasta_destino))
    else:
        pasta_scripts = pasta_destino  # fallback

    bat_path = os.path.join(PASTA_BASE, f"Launcher_{sistema}.bat")
    log_bat = r"C:\CIGS\execucao.log"
    target_script = os.path.join(pasta_scripts, script_nome)

    conteudo_bat = f"""@echo off
echo [%date% %time%] Iniciando Script >> "{log_bat}"
if exist "{target_script}" (
    cd /d "{pasta_scripts}"
    call "{script_nome}" {script_args} >> "{log_bat}"
    echo Sucesso >> "{log_bat}"
) else (
    echo ERRO: Script {script_nome} nao encontrado em {pasta_scripts} >> "{log_bat}"
)
exit
"""
    try:
        with open(bat_path, 'w') as f:
            f.write(conteudo_bat)
    except:
        return False, "Erro criar BAT"

    # ======================================
    # 4. AGENDAR NO WINDOWS (Task Scheduler)
    # ======================================
    try:
        if " " in data_hora:
            d_str, h_str = data_hora.split(" ")
        else:
            d_str = datetime.now().strftime("%d/%m/%Y")
            h_str = "03:00"
    
        task_name = f"CIGS_Update_{sistema.upper()}"
    
        # Usa o usuário e senha fornecidos se ambos estiverem preenchidos; caso contrário, usa SYSTEM
        if usuario and senha:
            cmd_sch = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONCE /sd {d_str} /st {h_str} /ru "{usuario}" /rp "{senha}" /rl HIGHEST /f'
        else:
            cmd_sch = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc ONCE /sd {d_str} /st {h_str} /ru SYSTEM /rl HIGHEST /f'
    
        res = subprocess.run(cmd_sch, shell=True, capture_output=True, text=True)
    
        if res.returncode == 0:
            log_debug(f"Agendamento realizado com SUCESSO: {task_name} com usuário {usuario if usuario else 'SYSTEM'}", sistema)
            return True, "Agendado"
        else:
            log_debug(f"Erro Schtasks: {res.stderr}", sistema)
            return False, f"Erro Task: {res.stderr}"
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
    log_debug("Iniciando cancelamento de missoes...")
    try:
        # 1. Lista todas as tarefas em formato CSV
        res = subprocess.run('schtasks /query /fo CSV /nh', shell=True, capture_output=True, text=True)
        if res.returncode != 0: return "Erro ao ler tarefas"
        
        count = 0
        # 2. Varre linha por linha procurando "CIGS_"
        for linha in res.stdout.splitlines():
            if "CIGS_" in linha:
                # Pega o nome da tarefa (primeira coluna, remove aspas)
                nome_tarefa = linha.split(',')[0].strip('"')
                log_debug(f"Matando tarefa: {nome_tarefa}")
                
                # 3. Deleta especificamente essa tarefa
                subprocess.run(f'schtasks /delete /tn "{nome_tarefa}" /f', shell=True)
                count += 1
        
        if count == 0: return "Nenhuma tarefa encontrada."
        return f"Abatidas {count} tarefas CIGS."
        
    except Exception as e:
        return f"Erro Abortar: {str(e)}"

def analisar_relatorio_deploy(sistema, data_filtro=None):
    """
    Lê o log do agente (CIGS_debug.log) e conta sucessos/erros 
    FILTRANDO pelo sistema (ex: [AC], [AG]).
    """
    # Importa aqui para evitar erro circular ou garanta que ARQUIVO_LOG_DEBUG está importado no topo
    from .config import ARQUIVO_LOG_DEBUG 
    
    total = 0; sucessos = 0; falhas = 0
    
    if not os.path.exists(ARQUIVO_LOG_DEBUG):
        return {"total": 0, "sucessos": 0, "falhas": 0, "porcentagem": 0}

    # Formata data para bater com o log (YYYY-MM-DD)
    data_fmt = None
    if data_filtro and len(data_filtro) == 8:
        data_fmt = f"{data_filtro[:4]}-{data_filtro[4:6]}-{data_filtro[6:]}"

    try:
        with open(ARQUIVO_LOG_DEBUG, "r", encoding="utf-8") as f:
            for line in f:
                # 1. Filtra pelo sistema (A chave do sucesso!)
                if f"[{sistema}]" not in line:
                    continue
                
                # 2. Filtra pela data (se informada)
                if data_fmt and data_fmt not in line:
                    continue

                # 3. Contabiliza
                if "Agendamento realizado com SUCESSO" in line:
                    sucessos += 1
                    total += 1
                elif "Erro" in line or "Falha" in line:
                    falhas += 1
                    total += 1
        
        p = int((sucessos/total)*100) if total > 0 else 0
        return {"total": total, "sucessos": sucessos, "falhas": falhas, "porcentagem": p}
    except:
        return {"total": 0, "sucessos": 0, "falhas": 0, "porcentagem": 0}