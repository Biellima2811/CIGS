import requests                     # Biblioteca para fazer requisições HTTP (GET/POST)
import os                           # Biblioteca para manipulação de arquivos/caminhos
import logging                      # Biblioteca para registrar logs em arquivo
from urllib.parse import urlparse, parse_qs   # Para analisar parâmetros de URLs
from datetime import datetime, timedelta, timezone  # Para manipular datas e fusos horários

class CIGSCore:
    def __init__(self):
        self.PORTA_AGENTE = 5580    # Porta padrão usada pelo agente nos servidores
        
        # Configuração inicial do Logger
        # Cria o arquivo 'cigs_ops.log'
        # Define o nível padrão como INFO
        # Formato de linha: data - nível - mensagem
        logging.basicConfig(
            filename='cigs_ops.log', 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )

    def registrar_log(self, mensagem, nivel="INFO"):
        """
        Registra mensagens no arquivo de log e devolve o texto formatado para exibir na GUI.
        """
        if nivel == "ERRO":
            logging.error(mensagem)   # Registra erro no arquivo
            prefix = "[❌ ERRO]"       # Prefixo exibido na GUI
        elif nivel == "SUCESSO":
            logging.info(mensagem)    # Registra informação positiva
            prefix = "[✅ OK]"
        else:
            logging.info(mensagem)    # Registra informação geral
            prefix = "[ℹ️ INFO]"
            
        timestamp = datetime.now().strftime("%H:%M:%S")  # Hora atual formatada
        return f"{timestamp} {prefix} {mensagem}"         # Retorna string para GUI

    def carregar_lista_ips(self, caminho_arquivo):
        """
        Lê o arquivo de lista de IPs fornecido pelo usuário.
        Ignora linhas vazias e comentários começando com '#'.
        """
        ips = []
        if not os.path.exists(caminho_arquivo):       # Verifica se o arquivo existe
            self.registrar_log(f"Arquivo não encontrado: {caminho_arquivo}", "ERRO")
            return []
        
        try:
            with open(caminho_arquivo, "r") as f:     # Abre o arquivo para leitura
                # Lê e filtra linhas válidas
                ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            self.registrar_log(f"Lista carregada: {len(ips)} servidores.")
            return ips
        except Exception as e:
            # Erro ao ler arquivo
            self.registrar_log(f"Erro ao ler arquivo: {e}", "ERRO")
            return []

    def checar_status_agente(self, ip, sistema="AC", full=False, timeout=3):
        """
        Consulta o agente do servidor e busca informações de status.
        
        Args:
            ip (str): Endereço IP do servidor
            sistema (str): Sistema alvo (AC, AG, PONTO, PATRIO)
            full (bool): Se True, inclui dados de disco e RAM
            timeout (int): Timeout em segundos (default: 3s)
        
        Returns:
            dict: Sempre contém 'ip' e 'status'
                Sucesso: status='ONLINE' + dados do agente
                Erro: status='OFFLINE'/'ERRO_API'/'TIMEOUT' + mensagem
        """
        try:
            # Monta URL com parâmetros
            url = f"http://{ip}:{self.PORTA_AGENTE}/cigs/status"
            params = {'sistema': sistema}
            if full:
                params['full'] = '1'
            
            # Timeout adaptativo: full=true precisa de mais tempo
            timeout_atual = timeout * 2 if full else timeout
            
            # Faz a requisição
            resp = requests.get(url, params=params, timeout=timeout_atual)
            
            # Trata diferentes status HTTP
            if resp.status_code == 200:
                dados = resp.json()
                return {
                    "ip": ip,
                    "status": "ONLINE",
                    "version": dados.get('version', '?'),
                    "hash": dados.get('hash'),
                    "clientes": dados.get('clientes', 0),
                    "ref": dados.get('ref', '-'),
                    "disk": dados.get('disk', '?') if full else None,
                    "ram": dados.get('ram', '?') if full else None,
                    "msg": None
                }
            elif resp.status_code == 404:
                return {
                    "ip": ip,
                    "status": "ERRO_API",
                    "msg": f"Rota não encontrada (404)",
                    "version": None, "hash": None, "clientes": 0, "ref": "-"
                }
            else:
                return {
                    "ip": ip,
                    "status": "ERRO_API",
                    "msg": f"HTTP {resp.status_code}",
                    "version": None, "hash": None, "clientes": 0, "ref": "-"
                }
                
        except requests.exceptions.Timeout:
            return {
                "ip": ip,
                "status": "TIMEOUT",
                "msg": f"Timeout após {timeout_atual}s",
                "version": None, "hash": None, "clientes": 0, "ref": "-"
            }
        except requests.exceptions.ConnectionError:
            return {
                "ip": ip,
                "status": "OFFLINE",
                "msg": "Conexão recusada",
                "version": None, "hash": None, "clientes": 0, "ref": "-"
            }
        except Exception as e:
            # Log do erro inesperado para diagnóstico
            print(f"[ERRO] checar_status_agente({ip}): {type(e).__name__} - {e}")
            return {
                "ip": ip,
                "status": "ERRO",
                "msg": f"{type(e).__name__}",
                "version": None, "hash": None, "clientes": 0, "ref": "-"
            }

    def enviar_ordem_agendamento(self, ip, url, arq, data, user, senha, sistema, modo, script="Executa.bat", params=""):
        """
        Envia ao agente uma ordem de agendamento de atualização, contendo:
        - url do pacote
        - arquivo
        - data/hora para execução
        - credenciais
        - sistema
        - script a executar
        - parâmetros opcionais
        """
        api = f"http://{ip}:{self.PORTA_AGENTE}/cigs/executar"
        
        # Calcula um caminho padrão de fallback para "Start In"
        sub = sistema if sistema != "PONTO" else "Ponto"
        path_padrao = rf"C:\Atualiza\CloudUp\CloudUpCmd\{sistema}\Atualizadores\{sub}"
        
        # Corpo enviado para o agente
        payload = {
            "url": url, 
            "arquivo": arq, 
            "data_hora": data,
            "user": user, 
            "pass": senha,
            "sistema": sistema,
            "start_in": path_padrao,
            "modo": modo,
            "script": script, 
            "params": params
        }
        
        try:
            r = requests.post(api, json=payload, timeout=60)  # Envia requisição POST
            if r.status_code == 200:
                resp = r.json()
                # Retorna sucesso/falha baseado no JSON
                return (True, resp.get('detalhe')) if resp.get('resultado') == "SUCESSO" else (False, resp.get('detalhe'))
            return False, f"Http {r.status_code}"
        except Exception as e:
            return False, str(e)
    
    def verificar_banco(self, ip, sistema):
        """
        Pede ao agente para rodar um check no banco Firebird.
        Pode demorar mais, por isso timeout maior.
        """
        try:
            r = requests.post(
                f"http://{ip}:{self.PORTA_AGENTE}/cigs/check_db", 
                json={'sistema': sistema}, 
                timeout=45
            )
            if r.status_code == 200:
                return r.json()                # JSON contendo status e log
            return {"status": "ERRO HTTP", "log": f"Status {r.status_code}"}
        except Exception as e:
            return {"status": "FALHA CONEXÃO", "log": str(e)}
    
    def verificar_validade_link(self, url):
        """
        Analisa links AWS S3 Presigned.
        Retorna se ele está válido, mensagem amigável e uma cor sugerida.
        """
        if not url:                                   # Verifica se link é vazio
            return False, 'Link vazio', "#95a5a6"
        
        try:
            parsed = urlparse(url)                    # Separa partes da URL
            params = parse_qs(parsed.query)           # Extrai parâmetros da query string

            # Detecta padrão de link Presigned AWS
            if 'X-Amz-Date' in params and 'X-Amz-Expires' in params:
                creation_str = params['X-Amz-Date'][0]   # Pega data de criação do link
                creation_dt = datetime.strptime(creation_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)

                expires_sec = int(params["X-Amz-Expires"][0])   # Tempo de expiração
                expiration_dt = creation_dt + timedelta(seconds=expires_sec)

                agora = datetime.now(timezone.utc)             # Hora atual em UTC
                restante = expiration_dt - agora               # Tempo restante

                if restante.total_seconds() > 0:
                    horas, resto = divmod(int(restante.total_seconds()), 3600)
                    minutos, _ = divmod(resto, 60)

                    if horas > 0:
                        msg = f'Link válido por: {horas}h:{minutos}min'
                    else:
                        msg = f'Link válido por: {minutos}min'
                    return True, msg, '#2ecc71'                 # Verde
                else:
                    return False, '⚠️ - Link EXPIRADO', '#e74c3c'

            # Outro tipo de link assinado com timestamp direto
            elif 'Expiration' in params:
                exp_ts = int(params['Expiration'][0])
                expiration_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
                agora = datetime.now(timezone.utc)

                if expiration_dt > agora:
                    return True, 'Link válido (Timestamp)', '#2ecc71'
                else:
                    return False, '⚠️ - Link EXPIRADO', '#e74c3c'
            else:
                return True, 'Link Público/Permanente', '#3498db'   # Link sem expiração
        except Exception as e:
            return False, f'Erro ao ler link: {str(e)}', '#e67e22'  # Laranja
    
    def obter_relatorio_agente(self, ip, sistema, data=None):
        """
        Solicita ao agente um relatório (status de execuções, logs, etc.).
        Pode opcionalmente filtrar por data.
        """
        url = f"http://{ip}:{self.PORTA_AGENTE}/cigs/relatorio?sistema={sistema}"
        if data:
            url += f"&data={data}"                     # Anexa filtro opcional
        
        try:
            r = requests.get(url, timeout=5)           # Requisição GET
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return {"erro": "Falha"}                       # Retorno padrão em falha
    
    def enviar_ordem_abortar(self, ip):
        """
        Envia comando para abortar a execução atual no agente.
        """
        try:
            r = requests.post(f"http://{ip}:{self.PORTA_AGENTE}/cigs/abortar", timeout=5)
            if r.status_code == 200:
                return True, r.json().get('detalhe')   # Sucesso
        except:
            pass
        return False, "Erro"                           # Falha

    def enviar_comando_bd(self, ip, motor, acao, db_path):
        """
        Envia ordem de manutenção de banco.
        Para MSSQL, envia o script T-SQL completo.
        Para Firebird, envia os comandos gfix/gbak.
        """
        script_sql = ""
        comando_cmd = ""
        
        if motor == "MSSQL":
            if acao == "MAINTENANCE":
                # SEU SCRIPT TOP AQUI (Com placeholder pro nome do banco)
                script_sql = f"""
                USE [{db_path}];
                GO
                PRINT '--- START CIGS MAINTENANCE ---';
                DBCC CHECKDB ('{db_path}') WITH NO_INFOMSGS;
                ALTER DATABASE CURRENT SET READ_COMMITTED_SNAPSHOT ON WITH ROLLBACK IMMEDIATE;
                ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON;
                
                DECLARE @tableName nvarchar(500), @indexName nvarchar(500), @percentFragment decimal(11,2);
                DECLARE FragmentedTableList cursor for
                SELECT object_name(indexstats.object_id), dbindexes.[name], indexstats.avg_fragmentation_in_percent
                FROM sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, NULL) AS indexstats
                INNER JOIN sys.tables dbtables ON dbtables.[object_id] = indexstats.[object_id]
                INNER JOIN sys.indexes dbindexes ON dbindexes.[object_id] = indexstats.[object_id] 
                AND indexstats.index_id = dbindexes.index_id
                WHERE indexstats.avg_fragmentation_in_percent > 5 AND indexstats.page_count > 10 AND dbindexes.[name] IS NOT NULL
                ORDER BY indexstats.page_count DESC;
                
                OPEN FragmentedTableList;
                FETCH NEXT FROM FragmentedTableList INTO @tableName, @indexName, @percentFragment;
                WHILE @@FETCH_STATUS = 0
                BEGIN
                    IF(@percentFragment BETWEEN 5 AND 30) EXEC('ALTER INDEX [' + @indexName + '] ON [' + @tableName + '] REORGANIZE;');
                    ELSE IF (@percentFragment > 30) EXEC('ALTER INDEX [' + @indexName + '] ON [' + @tableName + '] REBUILD;');
                    FETCH NEXT FROM FragmentedTableList INTO @tableName, @indexName, @percentFragment;
                END
                CLOSE FragmentedTableList; DEALLOCATE FragmentedTableList;
                PRINT '--- END CIGS MAINTENANCE ---';
                """
            elif acao == "CHECKDB":
                script_sql = f"DBCC CHECKDB ('{db_path}') WITH NO_INFOMSGS;"

            # O Agente precisa saber rodar SQL. Vamos assumir que ele salva num .sql e roda sqlcmd
            # Se o agente não tiver lógica de SQL, mandamos como comando CMD usando sqlcmd direto
            # Ex: sqlcmd -S localhost -E -Q "QUERY"
            # Como o script é grande, o ideal seria o Agente receber um tipo "SQL_EXEC".
            # Vou simplificar: Enviamos como 'CMD' chamando sqlcmd, mas o script é grande demais para linha de comando.
            # ESTRATÉGIA: Vamos mandar o agente salvar o arquivo e rodar.
            
            # Payload para o Agente (Assumindo que ele aceita 'script_content')
            payload = {
                "action": "SQL_MAINTENANCE",
                "db_name": db_path,
                "script": script_sql
            }

        elif motor == "FIREBIRD":
            # Traduz ações para comandos GFIX/GBAK
            user_pass = "-user SYSDBA -pass masterkey" # Padrão ou pegar da config
            if acao == "CHECK":
                comando_cmd = f'gfix -v -full "{db_path}" {user_pass}'
            elif acao == "MEND":
                comando_cmd = f'gfix -mend -full -ignore "{db_path}" {user_pass}'
            elif acao == "SWEEP":
                comando_cmd = f'gfix -sweep "{db_path}" {user_pass}'
            elif acao == "AUTO":
                # Envia um comando composto
                comando_cmd = f'gfix -mend -full -ignore "{db_path}" {user_pass} && gfix -sweep "{db_path}" {user_pass}'
            
            payload = {
                "action": "CMD_EXEC",
                "cmd": comando_cmd
            }

        # Envio Genérico (Você já tem a lógica de post no api.py ou aqui mesmo)
        try:
            url = f"http://{ip}:5578/cigs/exec"
            # Nota: Você precisará adaptar o endpoint do Agente se ele não tiver /cigs/exec genérico
            # Se usar o endpoint de agendamento existente, adapte os parâmetros.
            import requests
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return {"status": "OK", "msg": "Comando enviado."}
            else:
                return {"status": "ERRO", "msg": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "FALHA", "msg": str(e)}