import sqlite3
import json
from datetime import datetime
from core.security_manager import CIGSSecurity

class CIGSDatabase:
    def __init__(self, db_file='cigs_data.db'):
        self.db_file = db_file
        self.security = CIGSSecurity()
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def init_db(self):
        # Cria as tabelas se não existirem
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tabela de Servidores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servidores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                hostname TEXT,
                ip_publico TEXT,
                funcao TEXT,
                cliente TEXT,
                usuario_especifico TEXT,
                senha_especifica TEXT,
                criado_em DATETIME
            )
        """)
        
        # Tabela de Histórico (Para o Dashboard novo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_scan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora DATETIME,
                total INTEGER,
                online INTEGER,
                offline INTEGER,
                latencia_media REAL
            )
        """)
        conn.commit()
        conn.close()

    def adicionar_servidor(self, ip, host, pub, func, cli, usuario=None, senha=None):
        try:
            conn = self.get_connection()
            conn.execute("""
                INSERT INTO servidores (ip, hostname, ip_publico, funcao, cliente, usuario_especifico, senha_especifica, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ip, host, pub, func, cli , usuario, senha, datetime.now()))
            conn.commit()
            conn.close()
            # RETORNO CORRETO: (Booleano, String)
            return True, "Servidor Registrado com Sucesso."
            
        except sqlite3.IntegrityError:
            return False, "Erro: Este IP já está cadastrado."
            
        except Exception as e:
            return False, f"Erro BD: {str(e)}"
        
    def listar_servidores(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row # Para acessar por nome da coluna
        cursor = conn.execute('select * from servidores order by cliente, hostname')
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return dados

    def remover_servidor(self, ip):
        conn = self.get_connection()
        conn.execute('delete from servidores where ip = ?', (ip,))
        conn.commit()
        conn.close()

    # --- OPERAÇÕES DE HISTÓRICO (Para o Gráfico) ---
    def registrar_scan(self, total, on, off, latencia):
        try:
            conn = self.get_connection()
            # CORREÇÃO: Removemos a vírgula que criava a tupla errada e passamos os parâmetros direto no execute
            conn.execute("""
                INSERT INTO historico_scan (data_hora, total, online, offline, latencia_media)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), total, on, off, latencia))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def obter_historico_recente(self, limite=50):
        """Pega os últimos 50 scans para montar o gráfico de sinal"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM historico_scan ORDER BY id DESC LIMIT ?", (limite,))
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return dados[::-1] # Inverte para ficar cronológico
    
    def atualizar_servidor(self, ip_antigo, novo_ip, host, pub, func, cli, usuario=None, senha=None):
        try:
            conn = self.get_connection()
            conn.execute("""
                UPDATE servidores 
                SET ip = ?, hostname = ?, ip_publico = ?, funcao = ?, cliente = ?, usuario_especifico = ?, senha_especifica = ?
                WHERE ip = ?
            """, (novo_ip, host, pub, func, cli, usuario, senha, ip_antigo))
            conn.commit()
            conn.close()
            return True, 'Servidor atualizado com sucesso'
        except sqlite3.IntegrityError:
            return False, "Erro: O novo IP já está cadastrado em outro servidor"
        except Exception as e:
            return False, f'Erro BD: {str(e)}'
    
    def buscar_servidor_por_ip(self, ip):
        """Busca todos os dados de um servidor específico pelo IP"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM servidores WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None