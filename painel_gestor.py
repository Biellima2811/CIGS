import streamlit as st
import sqlite3
import pandas as pd
import os
import sys

# 1. Configura a página web
st.set_page_config(page_title="CIGS - Painel Executivo", layout="wide")
st.title("🐆 CIGS - Status da Infraestrutura")

# --- CORREÇÃO DO CAMINHO DO BANCO DE DADOS ---
# Identifica a pasta real onde o .exe foi executado (fora da pasta temporária do PyInstaller)
if getattr(sys, 'frozen', False):
    pasta_base = os.path.dirname(sys.executable)
else:
    pasta_base = os.path.dirname(os.path.abspath(__file__))

# Aponta para o arquivo CIGS_DB.db que deve estar na mesma pasta física do .exe
caminho_db = os.path.join(pasta_base, "CIGS_DB.db")

try:
    # 2. Conecta no banco correto
    conn = sqlite3.connect(caminho_db)

    # 3. Puxa os dados com a query
    # ATENÇÃO: Confirme se essas colunas realmente existem no seu CIGS_DB.db
    query = "SELECT ip, hostname, sistema, status, last_scan FROM servidores"
    df = pd.read_sql(query, conn)

    # 4. Cria métricas bonitas no topo da página
    total = len(df)
    
    # Verifica se a coluna 'status' existe antes de tentar contar
    if 'status' in df.columns:
        online = len(df[df['status'] == 'ONLINE'])
    else:
        online = 0
        
    offline = total - online

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Servidores", total)
    col2.metric("Servidores ONLINE", online)
    col3.metric("Servidores OFFLINE", offline)

    # 5. Mostra a tabela de dados na web
    st.subheader("Relatório Detalhado")
    st.dataframe(df, use_container_width=True)

except sqlite3.OperationalError as e:
    st.error("⚠️ Erro ao acessar o banco de dados.")
    st.warning(f"Verifique se o arquivo 'CIGS_DB.db' está nesta pasta: {caminho_db}")
except pd.errors.DatabaseError as e:
    st.error("⚠️ Erro ao ler a tabela no banco de dados.")
    st.warning("Verifique se as colunas (ip, hostname, sistema, status, last_scan) e a tabela 'servidores' realmente existem no seu CIGS_DB.db.")
    st.info(f"Detalhe técnico: {e}")
except Exception as e:
    st.error(f"⚠️ Ocorreu um erro inesperado: {e}")
finally:
    # Garante que a conexão com o banco seja fechada após o uso
    if 'conn' in locals():
        conn.close()