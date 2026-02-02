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
    caminho = MAPA_RAIZ.get(sistema.upper())
    if not caminho: return -1, "N/A"
    
    ini_paths = [os.path.join(caminho, "config.ini"), os.path.join(caminho, "Config", "config.ini")]
    arquivo_ini = next((p for p in ini_paths if os.path.exists(p)), None)
    
    if not arquivo_ini: return 0, "Sem INI"
    
    count = 0; ref = "N/A"
    try:
        with open(arquivo_ini, 'r', encoding='latin-1') as f:
            for l in f:
                if "Customer=" in l and not l.strip().startswith(";"):
                    count += 1
                    if count == 1:
                        try: ref = l.split("Customer=")[1].split(",")[0].strip()
                        except: pass
        return count, ref
    except: return 0, "Erro Ler"