import psycopg2
import psycopg2.extras # Para converter as linhas em dicionários (igual ao SQLite)
from datetime import datetime
from core.security_manager import CIGSSecurity
import bcrypt
import json

class CIGSDatabase:
    def __init__(self):
        # ==========================================
        # ⚙️ CREDENCIAIS DO NOVO COFRE (POSTGRESQL)
        # ==========================================
        self.db_params = {
            "host": "localhost",
            "database": "cigs_db",
            "user": "postgres",
            "password": "Fortes@1", # <--- COLOQUE A SUA SENHA AQUI ANTES DE RODAR
            "port": "5432"
        }
        self.security = CIGSSecurity()
        # Não precisamos mais criar tabelas aqui. O Migrador já construiu a base perfeita!
    
    def get_connection(self):
        return psycopg2.connect(**self.db_params)
    
    def adicionar_servidor(self, ip, host, pub, func, cli, usuario=None, senha=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # No PostgreSQL, usamos %s em vez de ?
            cursor.execute("""
                INSERT INTO servidores (ip, hostname, ip_publico, funcao, cliente, usuario_especifico, senha_especifica, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ip, host, pub, func, cli, usuario, senha, datetime.now()))
            conn.commit()
            return True, "Servidor Registrado com Sucesso."
        except psycopg2.IntegrityError:
            conn.rollback() # No Postgres, se a transação falhar, precisamos dar rollback
            return False, "Erro: Este IP já está cadastrado."
        except Exception as e:
            return False, f"Erro BD: {str(e)}"
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()
        
    def listar_servidores(self):
        conn = self.get_connection()
        # RealDictCursor simula o sqlite3.Row perfeitamente
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM servidores ORDER BY cliente, hostname')
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in dados]

    def remover_servidor(self, ip):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servidores WHERE ip = %s', (ip,))
        conn.commit()
        cursor.close()
        conn.close()

    # --- OPERAÇÕES DE HISTÓRICO (Para o Gráfico) ---
    def registrar_scan(self, total, on, off, latencia):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historico_scan (data_hora, total, online, offline, latencia_media)
                VALUES (%s, %s, %s, %s, %s)
            """, (datetime.now(), total, on, off, latencia))
            conn.commit()
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()
    
    def obter_historico_recente(self, limite=50):
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM historico_scan ORDER BY id DESC LIMIT %s", (limite,))
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in dados][::-1] 
    
    def atualizar_servidor(self, ip_antigo, novo_ip, host, pub, func, cli, usuario=None, senha=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE servidores 
                SET ip = %s, hostname = %s, ip_publico = %s, funcao = %s, cliente = %s, usuario_especifico = %s, senha_especifica = %s
                WHERE ip = %s
            """, (novo_ip, host, pub, func, cli, usuario, senha, ip_antigo))
            conn.commit()
            return True, 'Servidor atualizado com sucesso'
        except psycopg2.IntegrityError:
            conn.rollback()
            return False, "Erro: O novo IP já está cadastrado em outro servidor"
        except Exception as e:
            return False, f'Erro BD: {str(e)}'
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()
    
    def buscar_servidor_por_ip(self, ip):
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM servidores WHERE ip = %s", (ip,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None
    
    # --- GESTÃO DE USUÁRIOS E SEGURANÇA ---
    def criar_usuario(self, username, password, role='tecnico'):
        hash_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, %s)', 
                          (username, hash_pwd, role, datetime.now()))
            conn.commit()
            return True, 'Usuário criado com sucesso!'
        except psycopg2.IntegrityError:
            conn.rollback()
            return False, 'Erro: Nome de usuário já existe!'
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()
    
    def verificar_usuario(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), str(user['password_hash']).encode('utf-8')):
            return dict(user)
        return None