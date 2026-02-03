# Importa funções para manipulação de arquivos e caminhos
import os

# Importa subprocess, usado para executar comandos externos (como o isql)
import subprocess

# Importa variáveis definidas no config
from .config import MAPA_RAIZ, PASTA_BASE, ISQL_PATH

# Script SQL que será executado no Firebird para avaliar integridade básica do banco
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
    # Obtém caminho base onde fica o sistema informado (AC, AG, PONTO...)
    path_base = MAPA_RAIZ.get(sistema.upper())

    # Se o sistema não existir no mapa, retorna erro
    if not path_base:
        return {"status": "ERRO", "log": "Sistema desconhecido"}
    
    # Caminho do arquivo do banco (a ser detectado)
    banco_path = ""

    try:
        # Primeiro tenta localizar o arquivo config.ini dentro da raiz do sistema
        ini = os.path.join(path_base, "config.ini")

        # Caso o config.ini não esteja na raiz, tenta em "Config/config.ini"
        if not os.path.exists(ini):
            ini = os.path.join(path_base, "Config", "config.ini")

        # Se o arquivo de configuração foi encontrado
        if os.path.exists(ini):
            # Abre o arquivo INI com encoding latin-1
            with open(ini, 'r', encoding='latin-1') as f:
                # Percorre cada linha em busca da linha que contém o caminho do banco
                for l in f:
                    if "DatabaseName=" in l:
                        # Pega parte depois do sinal de igual
                        parts = l.split("=")[1].strip().split(":")
                        # Caso tenha formato "servidor:caminho", usa a última parte
                        banco_path = parts[-1] if len(parts) > 1 else parts[0]
                        break
    except:
        # Ignora falhas opcionais na leitura do arquivo
        pass

    # Se o banco não foi encontrado via config.ini,
    # tenta o caminho padrão: ...\DADOS\AC.FDB , por exemplo
    if not banco_path:
        banco_path = os.path.join(path_base, "DADOS", f"{sistema}.FDB")

    # Se o arquivo do banco não existe, retorna alerta
    if not os.path.exists(banco_path):
        return {"status": "ALERTA", "log": f"Banco 404: {banco_path}"}

    # Se o ISQL_PATH existir, usa ele; caso contrário, usa apenas "isql" esperando que esteja no PATH
    cmd_isql = f'"{ISQL_PATH}"' if os.path.exists(ISQL_PATH) else "isql"

    # Arquivo temporário onde será salvo o script SQL
    arquivo_sql = os.path.join(PASTA_BASE, "check_health.sql")
    
    try:
        # Grava o conteúdo do SCRIPT_SQL_CHECK dentro do arquivo SQL temporário
        with open(arquivo_sql, 'w') as f:
            f.write(SCRIPT_SQL_CHECK)

        # Monta o comando completo para executar o isql, passando usuário, senha, script e banco
        cmd = f'{cmd_isql} -user SYSDBA -password masterkey -i "{arquivo_sql}" "{banco_path}"'

        # Executa o comando com timeout de 60s e captura toda a saída
        res = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Se a saída contiver "OK" e não contiver "PROBLEMAS", considera status OK
        status = "OK" if "OK" in res.stdout and "PROBLEMAS" not in res.stdout else "ALERTA"

        # Retorna o status e todo o log retornado pelo isql
        return {"status": status, "log": res.stdout}
    
    except Exception as e:
        # Em caso de erro inesperado, retorna status ERRO com mensagem da exceção
        return {"status": "ERRO", "log": str(e)}
