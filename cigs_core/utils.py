# cigs_core/utils.py
import os
import sys
import hashlib
import subprocess
from datetime import datetime
from .config import ARQUIVO_LOG_DEBUG, PASTA_BASE, MAPA_RAIZ

def log_debug(msg):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        texto = f"[{ts}] {msg}"
        print(texto)
        if not os.path.exists(PASTA_BASE): os.makedirs(PASTA_BASE)
        with open(ARQUIVO_LOG_DEBUG, "a", encoding="utf-8") as f: 
            f.write(texto + "\n")
    except: pass

def ajustar_permissoes():
    try:
        subprocess.run(f'icacls "{PASTA_BASE}" /grant Todos:(OI)(CI)F /t /c /q', shell=True, stdout=subprocess.DEVNULL)
    except: pass

def get_self_hash():
    try:
        caminho = sys.executable
        if not getattr(sys, 'frozen', False):
            caminho = os.path.abspath(sys.modules['__main__'].__file__)
        if not os.path.exists(caminho): return 'dev_mode'

        h = hashlib.md5()
        with open(caminho, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''): h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        log_debug(f"Erro Hash: {e}")
        return 'erro_hash'

def contar_clientes(sistema):
    """
    Conta APENAS clientes ativos (sem ';') no config.ini.
    Usa a lógica estrita: Customer= na linha E linha não começa com ;
    """
    log_debug(f"--- Iniciando contagem (Lógica Estrita) para: {sistema} ---")
    
    # 1. Busca a pasta correta no config.py
    raiz = MAPA_RAIZ.get(sistema.upper())
    if not raiz: 
        log_debug(f"ERRO: Sistema {sistema} não mapeado no MAPA_RAIZ.")
        return 0, "Path N/A"

    # 2. Define onde procurar o ini
    paths = [
        os.path.join(raiz, "config.ini"),          # Raiz (Padrão novo)
        os.path.join(raiz, "Config", "config.ini") # Pasta Config (Legado)
    ]
    
    ini_path = None
    for p in paths:
        if os.path.exists(p):
            ini_path = p
            break
            
    if not ini_path:
        log_debug(f"ERRO: Nenhum config.ini encontrado em {raiz}")
        return 0, "Sem config.ini"

    log_debug(f"Lendo arquivo: {ini_path}")
    
    total_clientes = 0
    ref_cliente = "N/A"

    try:
        # 3. Abre com latin-1 para ler acentos de arquivos antigos
        with open(ini_path, 'r', encoding='latin-1') as f:
            for line in f:
                linha_limpa = line.strip()
                
                # A SUA LÓGICA DE OURO:
                # Tem "Customer="? E NÃO começa com ";"?
                if "Customer=" in line and not linha_limpa.startswith(";"):
                    total_clientes += 1
                    
                    if total_clientes == 1:
                        try:
                            # Pega o nome: Customer=NOME, -> split -> NOME
                            ref_cliente = line.split("Customer=")[1].split(",")[0].strip()
                        except:
                            ref_cliente = "Erro leitura"

        log_debug(f"Finalizado {sistema}: Encontrados {total_clientes} clientes ativos.")
        return total_clientes, ref_cliente

    except Exception as e:
        log_debug(f"ERRO ao ler arquivo: {str(e)}")
        return 0, f"Erro: {str(e)}"