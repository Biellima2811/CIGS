# Importa módulos padrão do Python para manipulação de caminhos, sistema, hashing,
# execução de comandos externos e datas.
import os
import sys
import hashlib
import subprocess
from datetime import datetime
# 1. ATUALIZE ESTA LINHA DE IMPORTAÇÃO (Adicione ARQUIVO_LOG_DEBUG)
from .config import PASTA_BASE, PASTA_DOWNLOAD, UNRAR_PATH, MAPA_RAIZ, get_caminho_atualizador, ARQUIVO_LOG_DEBUG


def log_debug(msg, sistema="GERAL"):
    """
    Registra mensagens de log com timestamp e tag do sistema.
    """
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Adiciona a TAG do sistema no log para permitir contagem separada
        texto = f"[{ts}] [{sistema}] {msg}"
        
        print(texto) # Debug no console

        if not os.path.exists(PASTA_BASE):
            os.makedirs(PASTA_BASE)

        with open(ARQUIVO_LOG_DEBUG, "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    except:
        pass


def ajustar_permissoes():
    try:
        # Executa o comando ICACLS no Windows para dar permissão FULL (F)
        # para o grupo "Todos" na pasta base, aplicando recursivamente (/t)
        # e suprimindo erros (/c /q).
        subprocess.run(
            f'icacls "{PASTA_BASE}" /grant Todos:(OI)(CI)F /t /c /q',
            shell=True,
            stdout=subprocess.DEVNULL
        )
    except:
        pass


def get_self_hash():
    try:
        # Pega o caminho do executável atual (EXE quando compilado)
        caminho = sys.executable

        # Se não estiver "frozen" (modo script .py), pega o arquivo .py principal
        if not getattr(sys, 'frozen', False):
            caminho = os.path.abspath(sys.modules['__main__'].__file__)

        # Se o arquivo não existir, assume modo desenvolvedor
        if not os.path.exists(caminho):
            return 'dev_mode'

        # Cria instância do MD5 para calcular hash do próprio arquivo
        h = hashlib.md5()

        # Abre o arquivo binário e lê-o em blocos de 4096 bytes
        with open(caminho, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)

        # Retorna hash MD5 final em hexadecimal
        return h.hexdigest()

    except Exception as e:
        # Se der erro, registra no log e retorna "erro_hash"
        log_debug(f"Erro Hash: {e}")
        return 'erro_hash'


def contar_clientes(sistema):
    """
    Conta APENAS clientes ativos no config.ini.
    Lógica estrita:
      - Conta linhas contendo "Customer="
      - Ignora linhas comentadas (que começam com ";")
    """
    sistema = sistema.upper().strip()

    # Log inicial da operação
    log_debug(f"--- Iniciando contagem para: {sistema} ---", sistema)
    
    # 1. Busca a pasta raiz correspondente ao sistema no MAPA_RAIZ
    raiz = MAPA_RAIZ.get(sistema.upper())

    # Se o sistema não existir no mapa, aborta
    if not raiz:
        log_debug(f"ERRO: Raiz não encontrada", sistema)
        return 0, "Path N/A"

    # 2. Lista os possíveis caminhos onde o config.ini pode estar
    paths = [
        os.path.join(raiz, "config.ini"),          # Padrão novo
        os.path.join(raiz, "Config", "config.ini") # Estrutura legado
    ]
    
    ini_path = None

    # Procura qual dos caminhos realmente existe
    for p in paths:
        if os.path.exists(p):
            ini_path = p
            break

    # Se nenhum foi encontrado, aborta
    if not ini_path:
        log_debug(f"ERRO: Nenhum config.ini encontrado em {raiz}")
        return 0, "Sem config.ini"

    # Log indicando qual arquivo será lido
    log_debug(f"Lendo arquivo: {ini_path}")
    
    total_clientes = 0   # Contador de clientes ativos
    ref_cliente = "N/A"  # Nome do primeiro cliente encontrado

    try:
        # 3. Abre o config.ini usando encoding latin-1 (compatível com arquivos antigos)
        with open(ini_path, 'r', encoding='latin-1') as f:
            for line in f:

                # Remove espaços e quebras para facilitar checagem de comentários
                linha_limpa = line.strip()
                
                # Verifica se a linha contém "Customer=" e NÃO é comentada
                if "Customer=" in line and not linha_limpa.startswith(";"):
                    total_clientes += 1

                    # Para o primeiro cliente encontrado, extrai o nome
                    if total_clientes == 1:
                        try:
                            # Divide linha e extrai texto após "Customer="
                            ref_cliente = line.split("Customer=")[1].split(",")[0].strip()
                        except:
                            ref_cliente = "Erro leitura"

        # Log final indicando quantos clientes foram encontrados
        log_debug(f"Finalizado {sistema}: Encontrados {total_clientes} clientes ativos.")

        # Retorna o total e o nome do primeiro cliente
        return total_clientes, ref_cliente

    except Exception as e:
        # Em caso de erro inesperado, registra e retorna falha
        log_debug(f"ERRO ao ler arquivo: {str(e)}")
        return 0, f"Erro: {str(e)}"

def analisar_relatorio_deploy(sistema, data_filtro=None):
    """
    Lê o log do agente (CIGS_debug.log) e conta sucessos/erros 
    FILTRANDO pelo sistema (ex: [AC], [AG]).
    """
    total = 0; sucessos = 0; falhas = 0
    
    if not os.path.exists(ARQUIVO_LOG_DEBUG):
        return {"total": 0, "sucessos": 0, "falhas": 0, "porcentagem": 0}

    # Formata data para bater com o log (YYYY-MM-DD)
    # A central manda YYYYMMDD, o log usa YYYY-MM-DD
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