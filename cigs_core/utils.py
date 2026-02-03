# Importa módulos padrão do Python para manipulação de caminhos, sistema, hashing,
# execução de comandos externos e datas.
import os
import sys
import hashlib
import subprocess
from datetime import datetime

# Importa variáveis globais definidas no config.py
from .config import ARQUIVO_LOG_DEBUG, PASTA_BASE, MAPA_RAIZ


def log_debug(msg):
    try:
        # Cria timestamp no formato YYYY-MM-DD HH:MM:SS
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Monta a frase final que será gravada
        texto = f"[{ts}] {msg}"
        
        # Exibe no console (útil para depuração)
        print(texto)

        # Se a pasta base não existir, cria (garante que o log consiga ser salvo)
        if not os.path.exists(PASTA_BASE):
            os.makedirs(PASTA_BASE)

        # Abre o arquivo de log no modo append ("a") e grava a mensagem
        with open(ARQUIVO_LOG_DEBUG, "a", encoding="utf-8") as f:
            f.write(texto + "\n")

    # Qualquer erro é ignorado para evitar exceções durante tentativa de log
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

    # Log inicial da operação
    log_debug(f"--- Iniciando contagem (Lógica Estrita) para: {sistema} ---")
    
    # 1. Busca a pasta raiz correspondente ao sistema no MAPA_RAIZ
    raiz = MAPA_RAIZ.get(sistema.upper())

    # Se o sistema não existir no mapa, aborta
    if not raiz:
        log_debug(f"ERRO: Sistema {sistema} não mapeado no MAPA_RAIZ.")
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
