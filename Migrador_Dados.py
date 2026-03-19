import sqlite3
import psycopg2

print("===================================================")
print("   C.I.G.S - OPERAÇÃO PONTE AÉREA (MIGRAÇÃO TOTAL)")
print("===================================================")

# ==========================================
# ⚙️ CONFIGURAÇÕES (AJUSTE AQUI)
# ==========================================
ARQUIVO_SQLITE = 'cigs_data.db' 

POSTGRES_HOST = "localhost"
POSTGRES_DB = "cigs_db"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "tec@123" # <--- COLOQUE A SENHA AQUI
POSTGRES_PORT = "5432"

try:
    print("\n[+] Estabelecendo conexões...")
    
    conn_sqlite = sqlite3.connect(ARQUIVO_SQLITE)
    cursor_sqlite = conn_sqlite.cursor()
    
    conn_pg = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    cursor_pg = conn_pg.cursor()

    print("[+] Conexões estabelecidas! Construindo as paredes do novo cofre...")

    # ==========================================
    # 🏗️ FASE 1: RECRIANDO SUAS TABELAS EXATAS
    # ==========================================
    
    # Tabela 1: Servidores (Idêntica ao seu db_manager.py)
    cursor_pg.execute("""
        CREATE TABLE IF NOT EXISTS servidores (
            id SERIAL PRIMARY KEY,
            ip VARCHAR(255) UNIQUE NOT NULL,
            hostname VARCHAR(255),
            ip_publico VARCHAR(255),
            funcao VARCHAR(255),
            cliente VARCHAR(255),
            usuario_especifico VARCHAR(255),
            senha_especifica VARCHAR(255),
            criado_em TIMESTAMP
        );
    """)

    # Tabela 2: Histórico para o Dashboard
    cursor_pg.execute("""
        CREATE TABLE IF NOT EXISTS historico_scan (
            id SERIAL PRIMARY KEY,
            data_hora TIMESTAMP,
            total INTEGER,
            online INTEGER,
            offline INTEGER,
            latencia_media REAL
        );
    """)

    # Tabela 3: Controle de Acesso (Usuários)
    cursor_pg.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'tecnico',
            created_at TIMESTAMP,
            last_login TIMESTAMP
        );
    """)
    conn_pg.commit()
    print("[+] Tabelas 'servidores', 'historico_scan' e 'users' prontas no PostgreSQL.")

    # ==========================================
    # 🚁 FASE 2: MIGRANDO SERVIDORES
    # ==========================================
    print("\n[+] Migrando tabela: SERVIDORES...")
    cursor_sqlite.execute("SELECT id, ip, hostname, ip_publico, funcao, cliente, usuario_especifico, senha_especifica, criado_em FROM servidores")
    servidores = cursor_sqlite.fetchall()
    
    for srv in servidores:
        cursor_pg.execute("""
            INSERT INTO servidores (id, ip, hostname, ip_publico, funcao, cliente, usuario_especifico, senha_especifica, criado_em) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, srv)
    print(f"    -> {len(servidores)} servidores migrados.")

    # ==========================================
    # 🚁 FASE 3: MIGRANDO DASHBOARD (HISTÓRICO)
    # ==========================================
    print("\n[+] Migrando tabela: HISTORICO_SCAN...")
    try:
        cursor_sqlite.execute("SELECT id, data_hora, total, online, offline, latencia_media FROM historico_scan")
        historico = cursor_sqlite.fetchall()
        
        for hist in historico:
            cursor_pg.execute("""
                INSERT INTO historico_scan (id, data_hora, total, online, offline, latencia_media) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, hist)
        print(f"    -> {len(historico)} registros de histórico migrados.")
    except sqlite3.OperationalError:
        print("    -> (Aviso) Tabela de histórico não encontrada ou vazia.")

    # ==========================================
    # 🚁 FASE 4: MIGRANDO USUÁRIOS
    # ==========================================
    print("\n[+] Migrando tabela: USERS...")
    try:
        cursor_sqlite.execute("SELECT id, username, password_hash, role, created_at, last_login FROM users")
        usuarios = cursor_sqlite.fetchall()
        
        for usu in usuarios:
            cursor_pg.execute("""
                INSERT INTO users (id, username, password_hash, role, created_at, last_login) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, usu)
        print(f"    -> {len(usuarios)} usuários migrados.")
    except sqlite3.OperationalError:
         print("    -> (Aviso) Tabela 'users' não encontrada ou vazia.")

    # Confirma todas as gravações
    conn_pg.commit()

    # ==========================================
    # ⚙️ SINCRONIZAÇÃO DE IDS (CRÍTICO)
    # ==========================================
    # Ajusta as catracas do Postgres para não gerarem IDs duplicados no futuro
    cursor_pg.execute("SELECT setval(pg_get_serial_sequence('servidores', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM servidores;")
    cursor_pg.execute("SELECT setval(pg_get_serial_sequence('historico_scan', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM historico_scan;")
    cursor_pg.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM users;")
    conn_pg.commit()

    print("\n[VITORIA] Missão cumprida! TODO O SISTEMA CIGS foi transferido para o PostgreSQL.")

except Exception as e:
    print(f"\n[!] ALERTA VERMELHO: A operação falhou: {e}")

finally:
    if 'cursor_sqlite' in locals(): cursor_sqlite.close()
    if 'conn_sqlite' in locals(): conn_sqlite.close()
    if 'cursor_pg' in locals(): cursor_pg.close()
    if 'conn_pg' in locals(): conn_pg.close()
    print("\nOperação finalizada.")