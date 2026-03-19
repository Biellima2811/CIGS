import psycopg2
import bcrypt
from datetime import datetime

POSTGRES_HOST = "localhost"
POSTGRES_DB = "cigs_db"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "tec@123" # <--- COLOQUE A SUA SENHA AQUI
POSTGRES_PORT = "5432"

print("=========================================")
print(" FORJANDO CREDENCIAIS DO COMANDANTE...")
print("=========================================")

try:
    # 1. Conecta direto no banco
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    cursor = conn.cursor()

    # 2. Criptografia militar para a senha "cigs123"
    print("[+] Criptografando a senha com bcrypt...")
    hash_pwd = bcrypt.hashpw('cigs123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 3. Injeta o Comandante no cofre
    cursor.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, %s)",
                   ('admin', hash_pwd, 'admin', datetime.now()))
    
    conn.commit()
    print("[VITORIA] Usuário 'admin' criado com sucesso! Senha temporária: cigs123")

except psycopg2.IntegrityError:
    conn.rollback()
    print("[!] O usuário 'admin' já existe no banco de dados!")
except Exception as e:
    print(f"[X] ERRO CRÍTICO: {e}")
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()