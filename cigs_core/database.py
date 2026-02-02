# cigs_core/database.py
import os
import subprocess
from .config import MAPA_RAIZ, PASTA_BASE, ISQL_PATH

SCRIPT_SQL_CHECK = """
SET NAMES WIN1252;
SET HEADING OFF;
SELECT 'SUMARIO' || '|' || 'Status Geral' || '|' ||
    CASE
        WHEN (SELECT COUNT(*) FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0 AND RDB$TRIGGER_INACTIVE = 1) > 0 THEN 'DIAGNOSTICO'
        WHEN (SELECT COUNT(*) FROM RDB$RELATION_CONSTRAINTS WHERE RDB$CONSTRAINT_TYPE = 'FOREIGN KEY' AND RDB$INDEX_NAME IS NULL) > 0 THEN 'DIAGNOSTICO'
        ELSE 'OK'
    END FROM RDB$DATABASE;
EXIT;
"""

def executar_check_banco(sistema):
    path_base = MAPA_RAIZ.get(sistema.upper())
    if not path_base: return {"status": "ERRO", "log": "Sistema desconhecido"}
    
    banco_path = ""
    try:
        ini = os.path.join(path_base, "config.ini")
        if not os.path.exists(ini): ini = os.path.join(path_base, "Config", "config.ini")
        if os.path.exists(ini):
            with open(ini, 'r', encoding='latin-1') as f:
                for l in f:
                    if "DatabaseName=" in l:
                        parts = l.split("=")[1].strip().split(":")
                        banco_path = parts[-1] if len(parts) > 1 else parts[0]
                        break
    except: pass

    if not banco_path:
        banco_path = os.path.join(path_base, "DADOS", f"{sistema}.FDB")

    if not os.path.exists(banco_path):
        return {"status": "ALERTA", "log": f"Banco 404: {banco_path}"}

    cmd_isql = f'"{ISQL_PATH}"' if os.path.exists(ISQL_PATH) else "isql"
    arquivo_sql = os.path.join(PASTA_BASE, "check_health.sql")
    
    try:
        with open(arquivo_sql, 'w') as f: f.write(SCRIPT_SQL_CHECK)
        cmd = f'{cmd_isql} -user SYSDBA -password masterkey -i "{arquivo_sql}" "{banco_path}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        status = "OK" if "OK" in res.stdout and "PROBLEMAS" not in res.stdout else "ALERTA"
        return {"status": status, "log": res.stdout}
    except Exception as e:
        return {"status": "ERRO", "log": str(e)}