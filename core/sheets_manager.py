# Importa a biblioteca gspread para manipular planilhas do Google Sheets
import gspread
# Importa o módulo de credenciais para autenticação via conta de serviço
from oauth2client.service_account import ServiceAccountCredentials
# Importa a classe datetime para trabalhar com data e hora
from datetime import datetime

# Classe responsável por gerenciar conexão e atualização das planilhas do Google Sheets
class CIGSSheets:
    def __init__(self):
        # Escopo de permissões necessárias para acessar o Google Sheets e Google Drive
        self.SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Nome do arquivo JSON que contém as credenciais da conta de serviço
        self.CREDENTIALS_FILE = 'credencials.json'
        # Cliente do gspread (será inicializado após autenticação)
        self.client = None

        # Dicionário que mapeia os sistemas para seus respectivos IDs de planilhas no Google Sheets
        self.SHEET_IDS = {
            "AC": "13yE4vD9EREKNtqh1UsUIVKyaZ6umnDvEZ7XSFXs-hBo",
            "AG": "1uwe3QrT499GRlnnfd2vFBsuaphhfxo8Yelgmunl7bGI",
            "PATRIO": "1tRo7lNOYMH-svqvMZYu_BueZM023vLvuuuPfc069-wQ",
            "PONTO": "1sovXviz0arQj-Q9kIKoZDa5u6e4HJAdxMqz882eIWjE"
        }

    def conectar(self):
        try:
            # Carrega as credenciais da conta de serviço a partir do arquivo JSON
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, self.SCOPE)
            # Autoriza o cliente gspread com as credenciais carregadas
            self.client = gspread.authorize(creds)
            # Retorna sucesso e mensagem de conexão
            return True, 'Conectado ao Google Drive'
        except Exception as e:
            # Caso ocorra erro, retorna False e a mensagem de erro
            return False, f'Erro ao conectar Google: {str(e)}'
    
    def atualizar_planilha(self, sistema, dados_relatorio):
        """
        Recebe lista de dados: [IP, Total, Sucessos, %, Log]
        E escreve na planilha correta.
        """
        # Se o cliente ainda não estiver conectado, tenta conectar
        if not self.client:
            ok, msg = self.conectar()
            # Se não conseguir conectar, retorna erro
            if not ok: return False, msg

        # Obtém o ID da planilha correspondente ao sistema informado
        sheet_id = self.SHEET_IDS.get(sistema.upper())
        # Se o sistema não estiver mapeado, retorna erro
        if not sheet_id: return False, 'Planilha não mapeada'

        try:
            # Abre a planilha pelo ID
            spreadsheet = self.client.open_by_key(sheet_id)
            # Seleciona a primeira aba da planilha (Sheet1)
            worksheet = spreadsheet.sheet1

            # Captura a data e hora atual formatada
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # Lista que armazenará as linhas a serem adicionadas
            linhas_para_adicionar = []

            # Itera sobre cada linha recebida no relatório
            for linha in dados_relatorio:
                # Monta a nova linha com o formato: [Data, IP, Clientes, Sucessos, %, Status Log]
                nova_linha = [data_hora] + linha
                # Adiciona a nova linha na lista
                linhas_para_adicionar.append(nova_linha)
            
            # Se houver linhas para adicionar, envia todas de uma vez (mais eficiente)
            if linhas_para_adicionar:
                worksheet.append_rows(linhas_para_adicionar)
            
            # Retorna sucesso e mensagem indicando quantas linhas foram enviadas
            return True, f'{len(linhas_para_adicionar)} linha enviadas para o Drive, Sistema : ({sistema})'
        
        except Exception as e:
            # Caso ocorra erro ao gravar na planilha, retorna False e mensagem de erro
            return False, f'Erro ao gravar na planilha: {str(e)}'
