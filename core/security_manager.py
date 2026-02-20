# Importa o módulo 'os' para manipulação de arquivos e diretórios
import os
# Importa o módulo 'json' para trabalhar com dados no formato JSON
import json
# Importa a classe Fernet da biblioteca 'cryptography' para criptografia simétrica
from cryptography.fernet import Fernet
import bcrypt

# Define a classe responsável pela segurança e armazenamento criptografado
class CIGSSecurity:
    def __init__(self):
        # Nome do arquivo onde as credenciais criptografadas serão salvas
        self.arquivo_config = 'CIGS_secrets.dat'
        # Nome do arquivo onde a chave de criptografia será armazenada
        self.arquivo_chave = 'CIGS.key'
        # Chama o método que carrega ou cria a chave de criptografia
        self.carregar_chave()
    
    def carregar_chave(self):
        """Carrega ou cria uma chave de criptografia única para este PC/Instalação"""
        # Verifica se o arquivo da chave já existe
        if not os.path.exists(self.arquivo_chave):
            # Se não existir, gera uma nova chave de criptografia
            self.chave = Fernet.generate_key()
            # Abre o arquivo da chave em modo de escrita binária
            with open(self.arquivo_chave, 'wb') as k:
                # Escreve a chave gerada dentro do arquivo
                k.write(self.chave)
        else:
            # Se o arquivo já existir, abre em modo leitura binária
            with open(self.arquivo_chave, 'rb') as k:
                # Lê a chave existente do arquivo
                self.chave = k.read()
        # Cria um objeto Fernet com a chave carregada para criptografar/descriptografar
        self.fernet = Fernet(self.chave)
    
    def salvar_credenciais(self, email, senha, smtp_server, smtp_port):
        # Cria um dicionário com os dados de login e servidor
        dados = {
            'email' : email,
            'senha' : senha,
            'server' : smtp_server,
            'port' : smtp_port
        }

        # Converte o dicionário em JSON -> transforma em bytes -> criptografa
        dados_json = json.dumps(dados).encode()
        dados_cripto = self.fernet.encrypt(dados_json)

        # Abre o arquivo de configuração em modo escrita binária
        with open(self.arquivo_config, 'wb') as f:
            # Escreve os dados criptografados no arquivo
            f.write(dados_cripto)
        # Retorna True indicando que o processo foi concluído com sucesso
        return True

    def obter_credenciais(self):
        # Verifica se o arquivo de configuração existe
        if not os.path.exists(self.arquivo_config):
            # Se não existir, retorna None (nenhuma credencial salva)
            return None
        
        try:
            # Abre o arquivo de configuração em modo leitura binária
            with open(self.arquivo_config, 'rb') as f:
                # Lê os dados criptografados do arquivo
                dados_cripto = f.read()

            # Descriptografa os dados -> transforma em string -> carrega como JSON
            dados_json = self.fernet.decrypt(dados_cripto).decode()
            return json.loads(dados_json)
        except:
            # Se ocorrer erro (chave errada ou arquivo corrompido), retorna None
            return None
    # --- NOVOS MÉTODOS PARA SENHA MESTRA ---
    ARQUIVO_SENHA = 'CIGS_master.dat'
    def definir_senha_mestra(self, senha):
        """Cria e armazena o hash da senha mestra (primeira execução)."""
        salt = bcrypt.gensalt()
        hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt)
        # Criptografa o hash antes de salvar
        hash_cripto = self.fernet.encrypt(hash_senha)
        with open(self.ARQUIVO_SENHA, 'wb') as f:
            f.write(hash_cripto)
        return True
    
    def verificar_senha_mestra(self, senha):
        """Verifica se a senha fornecida corresponde à hash armazenada."""
        if not os.path.exists(self.ARQUIVO_SENHA):
            return False
        
        try:
            with open(self.ARQUIVO_SENHA, 'rb') as f:
                hash_cripto = f.read()
            hash_senha = self.fernet.decrypt(hash_cripto)
            return bcrypt.checkpw(senha.encode('utf-8'), hash_senha)
        except:
            return False