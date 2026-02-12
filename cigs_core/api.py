# Importa a classe Flask para criar o servidor web, jsonify para respostas JSON e request para acessar dados enviados ao servidor
from flask import Flask, jsonify, request

# Importa módulo para manipular arquivos e obter informações de disco
import shutil

# Importa psutil para obter informações de uso de memória RAM
import psutil

# Importa constantes e funções de configuração do módulo interno config
from .config import PORTA, VERSAO_AGENTE, get_caminho_atualizador

# Importa utilidades internas, como logs, permissões e funções auxiliares
from .utils import log_debug, ajustar_permissoes, get_self_hash, contar_clientes

# Importa função para verificar banco de dados
from .database import executar_check_banco

# Importa tarefas executadas pelo agente
from .tasks import agendar_tarefa_universal, analisar_relatorio_deploy, cancelar_missao, sanitizar_extracao

# Cria a aplicação Flask
app = Flask(__name__)

# Define a rota /cigs/status para requisições GET
@app.route('/cigs/status', methods=['GET'])
def status():
    # Lê o parâmetro 'sistema' da URL; padrão é 'AC'
    sis = request.args.get('sistema', 'AC')

    # DEBUG NO LOG: Vamos ver quem está pedindo o quê
    # Isso vai aparecer no CIGS_debug.log do servidor
    log_debug(f"API /status chamada. Sistema solicitado: '{sis}'")
    
    # Verifica se deve retornar dados completos (uso de disco e RAM)
    # 'full=1' ativa modo detalhado
    full = request.args.get('full', '0') == '1'
    
    # Obtém quantidade de clientes e referência do sistema informado
    qtd, ref = contar_clientes(sis)

    # Variáveis default para dados de disco e memória
    d = 0; m = 0
    
    # Se o modo detalhado foi ativado
    if full:
        try:
            # Obtém espaço livre no disco C: convertido para GB
            d = round(shutil.disk_usage("C:\\").free / (1024**3), 2)
        except:
            pass
        try:
            # Obtém percentual de uso da memória RAM
            m = psutil.virtual_memory().percent
        except:
            pass
        
    # Retorna resposta JSON com informações do agente
    return jsonify({
        "status": "ONLINE",
        "version": VERSAO_AGENTE,
        "hash": get_self_hash(),
        "clientes": qtd,
        "ref": ref,
        "sistema_lido": sis,
        "disk": d,
        "ram": m
    })

# Define rota /cigs/executar para requisições POST
@app.route('/cigs/executar', methods=['POST'])
def executar():
    # Obtém JSON enviado na requisição
    d = request.json

    # Lê sistema informado; padrão é AC
    sist = d.get('sistema', 'AC')

    # Caminho onde o script deve iniciar; caso não venha, usa caminho padrão pelo sistema
    start_in = d.get('start_in') or get_caminho_atualizador(sist)

    # Script que a central deseja executar; padrão é "Executa.bat"
    script_alvo = d.get('script')
    # Se vier vazio ou None, usa o Padrão Executa.bat
    if not script_alvo:
        script_alvo = 'Executa.bat'
    # Argumentos adicionais para o script
    argumentos = d.get('params', '')

    # Agenda a tarefa usando função universal
    s, m = agendar_tarefa_universal(
        d.get('url'),
        d.get('arquivo'),
        d.get('data_hora'),
        d.get('user'),
        d.get('pass'),
        start_in,
        sist,
        d.get('modo'),
        script_nome=script_alvo,   # Nome do script a executar
        script_args=argumentos     # Argumentos passados ao script
    )
    
    # Se modo COMPLETO (que envolve download), realiza sanitização imediata da pasta
    if d.get('modo') == "COMPLETO" and start_in:
        sanitizar_extracao(start_in)

    # Retorna o resultado da execução para a central
    return jsonify({"resultado": "SUCESSO" if s else "ERRO", "detalhe": m})

# Rota responsável por checar o banco de dados
@app.route('/cigs/check_db', methods=['POST'])
def check_db():
    # Executa verificação do banco para o sistema informado
    return jsonify(executar_check_banco(request.json.get('sistema', 'AC')))

# Rota que retorna relatório do backup
@app.route('/cigs/relatorio', methods=['GET'])
def relatorio():
    sis = request.args.get('sistema', 'AC')
    data = request.args.get('data') # YYYYMMDD
    return jsonify(analisar_relatorio_deploy(sis, data))

# Rota para abortar uma tarefa em execução
@app.route('/cigs/abortar', methods=['POST'])
def abortar():
    # Cancela tarefa ativa
    res = cancelar_missao()

    # Retorna para a central que a missão foi abortada
    return jsonify({"resultado": "ABORTADO", "detalhe": res})

# Função que inicia o servidor Flask
def iniciar_servidor():
    # Registra uma mensagem de log indicando inicialização
    log_debug(f">>> CIGS AGENTE {VERSAO_AGENTE} INICIANDO NA PORTA {PORTA} <<<")

    # Ajusta permissões do ambiente antes de iniciar o servidor
    ajustar_permissoes()

    # Roda o servidor Flask acessível em qualquer IP local
    app.run(host='0.0.0.0', port=PORTA)
