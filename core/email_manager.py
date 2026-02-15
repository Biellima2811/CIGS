"""
CIGS Email Manager - Sistema completo de notificações
Desenvolvido por Gabriel Levi - Fortes Tecnologia 2026
"""

import smtplib
import logging
import os
import socket
import platform
import psutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import uptime
from typing import List, Dict, Optional, Tuple
import json
import threading
import time
from datetime import datetime, timedelta


class CIGSEmailManager:
    """
    Gerenciador de Notificações por Email do CIGS
    Suporte a múltiplos destinatários, templates HTML, anexos e agendamento
    """
    
    def __init__(self, security_manager):
        self.security = security_manager
        self.logger = logging.getLogger('CIGS_Email')
        self.configurar_logger()
        
        # Fila de emails para envio assíncrono
        self.fila_emails = []
        self.thread_envio = None
        self.ativo = True
        
        # Inicia thread de processamento da fila
        self.iniciar_processador_fila()
    
    def configurar_logger(self):
        """Configura logger específico para email"""
        handler = logging.FileHandler('cigs_email.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    # ==========================================
    # PROCESSAMENTO DE FILA (ASSÍNCRONO)
    # ==========================================
    
    def iniciar_processador_fila(self):
        """Inicia thread que processa a fila de emails"""
        def processar():
            while self.ativo:
                try:
                    if self.fila_emails:
                        # Pega o primeiro email da fila
                        email_data = self.fila_emails.pop(0)
                        self._enviar_email_sincrono(email_data)
                    time.sleep(1)  # Evita uso excessivo de CPU
                except Exception as e:
                    self.logger.error(f"Erro no processador de fila: {e}")
        
        self.thread_envio = threading.Thread(target=processar, daemon=True)
        self.thread_envio.start()
    
    # ==========================================
    # MÉTODOS PÚBLICOS
    # ==========================================
    
    def enviar_email_agendamento(self, sistema: str, data: str, hora: str, 
                                 num_servidores: int, clientes: int, 
                                 destinatarios: List[str] = None):
        """
        Envia notificação de agendamento de missão
        """
        creds = self.security.obter_credenciais()
        if not creds:
            self.logger.warning("Credenciais de email não configuradas")
            return False
        
        to_list = destinatarios or [creds['email']]
        
        assunto = f"🚀 CIGS - Missão Agendada: {sistema} - {data}"
        
        # Template HTML profissional
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2980b9, #2c3e50); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ecf0f1; padding: 20px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2980b9; }}
                .success {{ color: #27ae60; }}
                .warning {{ color: #e67e22; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #7f8c8d; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 MISSÃO AGENDADA</h1>
                    <p>Sistema: <strong>{sistema}</strong></p>
                </div>
                <div class="content">
                    <div class="info-box">
                        <h3>📅 Data e Hora</h3>
                        <p><strong>Data:</strong> {data}</p>
                        <p><strong>Hora:</strong> {hora}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3>📊 Estatísticas</h3>
                        <p><strong>Servidores alvo:</strong> {num_servidores}</p>
                        <p><strong>Total de clientes:</strong> {clientes}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3>🖥️ Servidor de Origem</h3>
                        <p><strong>Hostname:</strong> {socket.gethostname()}</p>
                        <p><strong>IP Local:</strong> {self._get_local_ip()}</p>
                    </div>
                    
                    <p style="color: #27ae60; font-weight: bold;">✅ Missão programada com sucesso no Task Scheduler!</p>
                </div>
                <div class="footer">
                    <p>CIGS - Central de Comandos Integrados v3.4</p>
                    <p>© Fortes Tecnologia - {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        texto_plano = f"""
        CIGS - Missão Agendada
        
        Sistema: {sistema}
        Data: {data}
        Hora: {hora}
        
        Servidores alvo: {num_servidores}
        Total de clientes: {clientes}
        
        Servidor de origem: {socket.gethostname()}
        IP: {self._get_local_ip()}
        
        Status: ✅ MISSÃO AGENDADA COM SUCESSO
        """
        
        email_data = {
            'to': to_list,
            'subject': assunto,
            'html': html_body,
            'text': texto_plano,
            'attachments': []
        }
        
        self.fila_emails.append(email_data)
        self.logger.info(f"Email de agendamento enfileirado para {sistema}")
        return True
    
    def enviar_email_relatorio_completo(self, sistema: str, stats: Dict, 
                                        csv_path: str = None, log_path: str = None,
                                        destinatarios: List[str] = None):
        """
        Envia relatório completo com estatísticas detalhadas e anexos
        """
        creds = self.security.obter_credenciais()
        if not creds:
            return False
        
        to_list = destinatarios or [creds['email']]
        
        assunto = f"📊 CIGS - Relatório Completo: {sistema} - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Calcula métricas
        taxa_sucesso = (stats.get('sucessos', 0) / stats.get('total', 1)) * 100
        uptime = self._calcular_uptime()
        memoria = psutil.virtual_memory()
        disco = psutil.disk_usage('C:\\')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #27ae60, #229954); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ecf0f1; padding: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
                .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
                .stat-label {{ font-size: 12px; color: #7f8c8d; }}
                .success {{ color: #27ae60; }}
                .warning {{ color: #e67e22; }}
                .danger {{ color: #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background: #34495e; color: white; padding: 10px; }}
                td {{ padding: 8px; border-bottom: 1px solid #bdc3c7; }}
                .footer {{ margin-top: 20px; font-size: 11px; color: #7f8c8d; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📈 RELATÓRIO DE OPERAÇÕES</h1>
                    <p>Sistema: <strong>{sistema}</strong></p>
                    <p>Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="content">
                    <h2>🎯 Estatísticas da Missão</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('total', 0)}</div>
                            <div class="stat-label">Total de Execuções</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #27ae60;">{stats.get('sucessos', 0)}</div>
                            <div class="stat-label">Sucessos</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #e74c3c;">{stats.get('falhas', 0)}</div>
                            <div class="stat-label">Falhas</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{taxa_sucesso:.1f}%</div>
                            <div class="stat-label">Taxa de Sucesso</div>
                        </div>
                    </div>
                    
                    <h2>📋 Detalhamento por Servidor</h2>
                    <table>
                        <tr>
                            <th>Servidor</th>
                            <th>Status</th>
                            <th>Clientes</th>
                            <th>Resultado</th>
                        </tr>
        """
        
        # Adiciona linhas da tabela com os dados dos servidores
        for servidor in stats.get('servidores', []):
            cor_status = "#27ae60" if servidor.get('status') == "ONLINE" else "#e74c3c"
            html_body += f"""
                        <tr>
                            <td>{servidor.get('ip', '-')}</td>
                            <td style="color: {cor_status}; font-weight: bold;">{servidor.get('status', '-')}</td>
                            <td>{servidor.get('clientes', 0)}</td>
                            <td>{servidor.get('resultado', '-')}</td>
                        </tr>
            """
        
        html_body += f"""
                    </table>
                    
                    <h2>💻 Saúde da Central</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{uptime}</div>
                            <div class="stat-label">Uptime</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{memoria.percent}%</div>
                            <div class="stat-label">RAM</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{disco.free // (1024**3)} GB</div>
                            <div class="stat-label">Disco Livre</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{socket.gethostname()}</div>
                            <div class="stat-label">Hostname</div>
                        </div>
                    </div>
                    
                    <h2>📎 Anexos</h2>
                    <ul>
                        <li>📊 Relatório CSV detalhado</li>
                        <li>📋 Logs de execução</li>
                    </ul>
                    
                    <p style="margin-top: 20px; font-weight: bold; color: #27ae60;">
                        ✅ Operação concluída com sucesso!
                    </p>
                </div>
                
                <div class="footer">
                    <p>CIGS - Central de Comandos Integrados v3.4</p>
                    <p>Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p>© Fortes Tecnologia - Desenvolvido por Gabriel Levi</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        texto_plano = f"""
        ========================================
        CIGS - RELATÓRIO COMPLETO DE OPERAÇÕES
        ========================================
        
        Sistema: {sistema}
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        📊 ESTATÍSTICAS:
        - Total de execuções: {stats.get('total', 0)}
        - Sucessos: {stats.get('sucessos', 0)}
        - Falhas: {stats.get('falhas', 0)}
        - Taxa de sucesso: {taxa_sucesso:.1f}%
        
        💻 SERVIDOR DE ORIGEM:
        - Hostname: {socket.gethostname()}
        - IP: {self._get_local_ip()}
        - Uptime: {uptime}
        - RAM: {memoria.percent}%
        - Disco livre: {disco.free // (1024**3)} GB
        
        📎 Anexos:
        - {os.path.basename(csv_path) if csv_path else 'CSV não gerado'}
        - {os.path.basename(log_path) if log_path else 'Log não anexado'}
        
        ========================================
        CIGS - Central de Comandos Integrados v3.4
        © Fortes Tecnologia - {datetime.now().year}
        """
        
        anexos = []
        if csv_path and os.path.exists(csv_path):
            anexos.append(csv_path)
        if log_path and os.path.exists(log_path):
            anexos.append(log_path)
        
        email_data = {
            'to': to_list,
            'subject': assunto,
            'html': html_body,
            'text': texto_plano,
            'attachments': anexos
        }
        
        self.fila_emails.append(email_data)
        self.logger.info(f"Relatório completo enfileirado para {sistema}")
        return True
    
    def enviar_email_alerta(self, sistema: str, servidor: str, 
                           erro: str, criticidade: str = "ALTA"):
        """
        Envia alerta de erro crítico
        """
        creds = self.security.obter_credenciais()
        if not creds:
            return False
        
        cores = {"ALTA": "#e74c3c", "MÉDIA": "#e67e22", "BAIXA": "#f1c40f"}
        cor = cores.get(criticidade.upper(), "#e74c3c")
        
        assunto = f"🚨 CIGS - ALERTA {criticidade}: {sistema} - {servidor}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background: {cor}; color: white; padding: 20px; border-radius: 10px; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h1>🚨 ALERTA DE SISTEMA</h1>
                <h2>Criticidade: {criticidade}</h2>
            </div>
            <div class="content">
                <h3>Sistema: {sistema}</h3>
                <h3>Servidor: {servidor}</h3>
                <h3>Erro:</h3>
                <pre style="background: #2c3e50; color: white; padding: 15px;">{erro}</pre>
                <p>Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        email_data = {
            'to': [creds['email']],
            'subject': assunto,
            'html': html_body,
            'text': f"ALERTA {criticidade}: {sistema} - {servidor}\n\nErro: {erro}",
            'attachments': []
        }
        
        self.fila_emails.append(email_data)
        self.logger.warning(f"Alerta enfileirado: {sistema} - {servidor} - {criticidade}")
        return True
    
    # ==========================================
    # MÉTODOS PRIVADOS
    # ==========================================
    
    def _enviar_email_sincrono(self, email_data: Dict):
        """
        Envia email de forma síncrona (usado pela fila)
        """
        creds = self.security.obter_credenciais()
        if not creds:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data['subject']
            msg['From'] = creds['email']
            msg['To'] = ', '.join(email_data['to'])
            
            # Anexa versão texto
            if 'text' in email_data:
                msg.attach(MIMEText(email_data['text'], 'plain', 'utf-8'))
            
            # Anexa versão HTML
            if 'html' in email_data:
                msg.attach(MIMEText(email_data['html'], 'html', 'utf-8'))
            
            # Anexa arquivos
            for anexo in email_data.get('attachments', []):
                if os.path.exists(anexo):
                    with open(anexo, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(anexo)}"'
                        )
                        msg.attach(part)
            
            # Envia
            server = smtplib.SMTP(creds['server'], int(creds['port']))
            server.starttls()
            server.login(creds['email'], creds['senha'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email enviado: {email_data['subject']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Falha no envio de email: {e}")
            return False
    
    def _get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _calcular_uptime(self):
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            return str(timedelta(seconds=int(uptime_seconds)))
        except:
            return "N/A"
    
    def parar(self):
        """Para o processador de fila"""
        self.ativo = False
        if self.thread_envio:
            self.thread_envio.join(timeout=5)