# cigs_core/api.py
from flask import Flask, jsonify, request
import shutil
import psutil

from .config import PORTA, VERSAO_AGENTE, get_caminho_atualizador
from .utils import log_debug, ajustar_permissoes, get_self_hash, contar_clientes
from .database import executar_check_banco
from .tasks import agendar_tarefa_universal, analisar_log_backup, cancelar_missao, sanitizar_extracao

app = Flask(__name__)

@app.route('/cigs/status', methods=['GET'])
def status():
    sis = request.args.get('sistema', 'AC')
    # Verifica se a central pediu dados pesados (full=1)
    full = request.args.get('full', '0') == '1'
    
    qtd, ref = contar_clientes(sis)
    d = 0; m = 0
    
    if full:
        try: d = round(shutil.disk_usage("C:\\").free / (1024**3), 2)
        except: pass
        try: m = psutil.virtual_memory().percent
        except: pass
        
    return jsonify({
        "status": "ONLINE", "version": VERSAO_AGENTE, "hash": get_self_hash(),
        "clientes": qtd, "ref": ref, "disk": d, "ram": m
    })

@app.route('/cigs/executar', methods=['POST'])
def executar():
    d = request.json
    sist = d.get('sistema', 'AC')
    
    # Tenta obter o start_in do JSON, se não tiver, calcula o correto
    start_in = d.get('start_in')
    if not start_in:
        start_in = get_caminho_atualizador(sist)

    s, m = agendar_tarefa_universal(
        d.get('url'), d.get('arquivo'), d.get('data_hora'), 
        d.get('user'), d.get('pass'), start_in, 
        sist, d.get('modo')
    )

    return jsonify({"resultado": "SUCESSO" if s else "ERRO", "detalhe": m})

@app.route('/cigs/check_db', methods=['POST'])
def check_db():
    return jsonify(executar_check_banco(request.json.get('sistema', 'AC')))

@app.route('/cigs/relatorio', methods=['GET'])
def relatorio():
    return jsonify(analisar_log_backup(request.args.get('sistema', 'AC')))

@app.route('/cigs/abortar', methods=['POST'])
def abortar():
    res = cancelar_missao()
    return jsonify({"resultado": "ABORTADO", "detalhe": res})

def iniciar_servidor():
    log_debug(f">>> CIGS AGENTE {VERSAO_AGENTE} INICIANDO NA PORTA {PORTA} <<<")
    ajustar_permissoes()
    app.run(host='0.0.0.0', port=PORTA)