import requests                     # Biblioteca para fazer requisições HTTP (GET/POST)
import os                           # Biblioteca para manipulação de arquivos/caminhos
import logging                      # Biblioteca para registrar logs em arquivo
from urllib.parse import urlparse, parse_qs   # Para analisar parâmetros de URLs
from datetime import datetime, timedelta, timezone  # Para manipular datas e fusos horários

class CIGSCore:
    def __init__(self):
        self.PORTA_AGENTE = 5578    # Porta padrão usada pelo agente nos servidores
        
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

    def checar_status_agente(self, ip, sistema, **kwargs):
        """
        Consulta o agente do servidor e busca informações como:
        - versão
        - disk, ram
        - hash
        Pode receber o parâmetro optional full=True para expandir dados.
        """
        try:
            # Monta a URL base sempre incluindo o sistema
            url = f"http://{ip}:{self.PORTA_AGENTE}/cigs/status?sistema={sistema}"
            
            # Caso 'full=True' tenha sido passado, adiciona na URL
            if kwargs.get('full'):
                url += "&full=1"

            print(f"[DEBUG] Consultando: {url}")  # Log para depuração no console

            r = requests.get(url, timeout=2)      # Envia requisição GET
            if r.status_code == 200:
                d = r.json()                      # Converte resposta para JSON
                return {
                    "ip": ip,
                    "status": "ONLINE",
                    "version": d.get('version', '?'), 
                    "hash": d.get('hash'),
                    "clientes": d.get('clientes', 0),
                    "ref": d.get('ref', '-'),
                    "disk": d.get('disk', '?'),
                    "ram": d.get('ram', '?')
                }
            # Caso o status não seja 200
            return {"ip": ip, "status": "ERRO API", "msg": str(r.status_code)}
        except:
            # Timeout ou erro de conexão
            return {"ip": ip, "status": "OFFLINE", "msg": "Timeout"}

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
