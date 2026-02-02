import sys
from cigs_core.api import iniciar_servidor
from cigs_core.tasks import sanitizar_extracao

if __name__ == '__main__':
    # Se receber argumentos, atua como ferramenta de linha de comando
    if len(sys.argv) > 2 and sys.argv[1] == '--sanitize':
        # Modo Limpeza: Chamado pelo BAT após o UnRAR
        caminho_alvo = sys.argv[2]
        sanitizar_extracao(caminho_alvo)
    else:
        # Modo Servidor: Inicia a API (Padrão)
        iniciar_servidor()