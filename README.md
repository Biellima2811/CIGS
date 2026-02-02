Markdown# 🐆 CIGS - Central de Comandos Integrados (v2.6)

> **"A selva nos une, a tecnologia nos protege."**

O **CIGS** é uma plataforma de orquestração tática para gerenciamento de servidores Windows em massa. Ele permite a atualização remota de sistemas, monitoramento de saúde (Hardware/Banco de Dados), execução de scripts sob demanda e geração de relatórios operacionais.

---

## 🚀 Funcionalidades Principais

* **Disparo Cirúrgico:** Atualize 1 ou 100 servidores simultaneamente com precisão.
* **Modos de Operação:**
    * **Full Update:** Baixa pacotes da nuvem (AWS S3), extrai e atualiza.
    * **Rede Local:** Copia executáveis da rede interna para servidores com restrição de internet.
    * **Sob Demanda:** Executa scripts específicos (`ExecutaOnDemand.bat`) com parâmetros personalizados (ex: lista de clientes).
* **Agendador Limpo:** Cria tarefas no Windows com nomes padronizados, evitando poluição do agendador.
* **Sanitização Automática:** Corrige extrações de arquivos `.rar` que criam subpastas indesejadas.
* **Monitoramento em Tempo Real:** Visualiza CPU, RAM, Disco e Versão do Agente direto da Central.
* **Check-up de Banco de Dados:** Executa diagnósticos remotos em bancos Firebird.

---

## 🏗️ Arquitetura do Sistema

O sistema é dividido em dois módulos estratégicos:

### 1. A Central (`CIGS_Central.exe`)
* **Interface Gráfica (GUI):** Desenvolvida em Python (Tkinter/TTKThemes).
* **Função:** Atua como o "Comandante". Envia ordens HTTP (JSON) para os agentes.
* **Localização:** Roda na máquina do analista/administrador.

### 2. O Agente (`CIGS_Agent.exe`)
* **Serviço Oculto:** Desenvolvido em Python (Flask) compilado com Nuitka.
* **Função:** Atua como o "Soldado". Recebe ordens, baixa arquivos, manipula o Windows Task Scheduler e acessa o banco de dados.
* **Localização:** Instalado como Serviço Windows em cada servidor cliente.

---

## 📂 Estrutura de Código (Onde está o quê?)

```text
CIGS/
├── main.py                 # Ponto de entrada da Central
├── CIGS_Agent.py           # Ponto de entrada do Agente
│
├── gui/                    # [INTERFACE] Tudo que é visual
│   ├── main_window.py      # Janela Principal e Lógica de Orquestração
│   └── panels/             # Painéis modulares (Topo, Infra, Dashboard, DB)
│
├── core/                   # [CÉREBRO DA CENTRAL]
│   ├── network_ops.py      # Comunicação HTTP com os Agentes
│   ├── security_manager.py # Criptografia de senhas (SMTP)
│   └── sheets_manager.py   # Integração com Google Sheets
│
└── cigs_core/              # [CÉREBRO DO AGENTE]
    ├── api.py              # Rotas do Servidor Web (Flask)
    ├── tasks.py            # Lógica Pesada (Download, BAT, Agendamento)
    ├── database.py         # Scripts SQL e Check-up Firebird
    ├── config.py           # Caminhos e Constantes
    └── utils.py            # Logs e Ferramentas Auxiliares
🛠️ Como Compilar (Forja das Armas)Pré-requisitosPython 3.12+Bibliotecas: flask, requests, psutil, cryptography, ttkthemes, gspreadFerramentas Externas na raiz: nssm.exe, UnRAR.exe1. Compilar o Agente (Modo Blindado)Usa Nuitka para performance e ofuscação.PowerShellpython -m nuitka --standalone --remove-output --windows-icon-from-ico=assets/onca_pintada.ico --include-package=cigs_core --include-package=cryptography -o CIGS_Agent.exe CIGS_Agent.py
Gera a pasta CIGS_Agent.dist.2. Compilar a Central (Modo Portátil)Usa PyInstaller para criar um executável único.PowerShellpyinstaller --noconsole --onefile --name="CIGS_Central_v2.6" --icon="assets/CIGS.ico" --collect-all ttkthemes --collect-all cryptography main.py
⚔️ Guia de Operação (Deploy)Coloque CIGS_Central_v2.6.exe, a pasta CIGS_Agent.dist, nssm.exe e UnRAR.exe na mesma pasta.Abra a Central.Carregue a lista de IPs (Lista_Ips.txt).Clique em "🛠️ Migrar Agente" para instalar/atualizar o serviço nos servidores remotos.Preencha os dados no Painel Superior (Link S3, Sistema, Script).Clique em "🚀 PREPARAR MISSÃO" e siga o checklist.🐛 Troubleshooting (Resolução de Problemas)SintomaCausa ProvávelSoluçãoCentral trava ao abrirConflito de Layout (Pack vs Grid)Verifique gui/main_window.py. Use apenas Grid.Agente não iniciaFalta do __init__.pyCrie um arquivo vazio __init__.py na pasta cigs_core.Erro "Executável não encontrado"Caminho errado no AgenteVerifique cigs_core/config.py e os caminhos mapeados.Pasta "AtualizaPonto" criada erradaFalha na SanitizaçãoO comando --sanitize falhou. Verifique cigs_core/tasks.py.Desenvolvido pela Divisão de Infraestrutura Nuvem - 2026
---

### 2. 🧠 Mapa Mental do Código (Para Manutenção)

Use este diagrama para se localizar rapidamente. Se algo der errado, vá direto ao "Setor" responsável.

#### 🎯 **OBJETIVO: Onde está o erro?**

**1. "A Interface da Central está feia, travando ou o botão não faz nada."**
* 📍 **Setor:** `gui/`
* **Arquivo:** `main_window.py` (Lógica dos botões, fluxo de telas) ou `gui/panels/*.py` (Elementos visuais específicos).
* *Dica:* Se for erro de layout ("cannot use geometry manager..."), é mistura de `.pack()` e `.grid()`.

**2. "A Central diz que enviou, mas o Agente não recebeu nada."**
* 📍 **Setor:** `core/` (Logística)
* **Arquivo:** `network_ops.py`
* *O que olhar:* Verifique a função `enviar_ordem_agendamento`. O payload JSON está montado certo? O IP está correto?

**3. "O Agente recebe o comando, mas dá erro 500 ou não faz nada."**
* 📍 **Setor:** `cigs_core/` (No servidor remoto)
* **Arquivo:** `api.py`
* *O que olhar:* É a porta de entrada. Veja se a rota `/executar` está recebendo os dados corretamente.

**4. "O arquivo baixa, mas a pasta fica bagunçada (Ex: `AC\AtualizaAC`)."**
* 📍 **Setor:** `cigs_core/`
* **Arquivo:** `tasks.py` -> Função `sanitizar_extracao`.
* *Lógica:* É aqui que ele move os arquivos para cima e apaga a subpasta. Verifique se o `CIGS_Agent.py` está recebendo o argumento `--sanitize` no BAT gerado.

**5. "O Agendamento no Windows cria 1000 tarefas com nomes estranhos."**
* 📍 **Setor:** `cigs_core/`
* **Arquivo:** `tasks.py` -> Função `agendar_tarefa_universal`.
* *Correção:* Verifique a variável `task_name`. Ela deve ser fixa (ex: `CIGS_Atualizacao_Full_AC`) para sobrescrever a anterior.

**6. "O Banco de Dados diz que está OK, mas não está."**
* 📍 **Setor:** `cigs_core/`
* **Arquivo:** `database.py`.
* *O que olhar:* Verifique o `SCRIPT_SQL_CHECK`. É lá que a query de diagnóstico é montada.

---

### 🧭 Fluxo da Missão (Passo a Passo no Código)

1.  **Usuário:** Clica em "Disparar" na Central.
2.  **`gui/main_window.py`:** Coleta dados do `TopPanel` e chama `worker_disparo`.
3.  **`core/network_ops.py`:** Envia `POST http://IP:5578/cigs/executar` com JSON `{script: "...", params: "..."}`.
4.  **`cigs_core/api.py` (Agente):** Recebe o JSON e chama `agendar_tarefa_universal`.
5.  **`cigs_core/tasks.py`:**
    * Cria o arquivo `Launcher_AC.bat`.
    * Escreve no BAT: "Extraia -> Rode `CIGS_Agent --sanitize` -> Rode `call Executa.bat`".
    * Roda comando `schtasks /create ... /tn "CIGS_Full_AC"`.
6.  **Windows:** Executa a tarefa agendada.
