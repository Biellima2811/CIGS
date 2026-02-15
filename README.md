# 🐆 CIGS - Central de Comandos Integrados

**Versão 3.4**  
*"A selva nos une, a tecnologia nos protege."*

O **CIGS** é uma plataforma de orquestração tática para gerenciamento de servidores Windows em massa. Ele permite a atualização remota de sistemas, monitoramento de saúde (hardware/banco de dados), execução de scripts sob demanda e geração de relatórios operacionais, tudo através de uma interface gráfica amigável e uma arquitetura cliente-servidor robusta.

---

## 📌 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Requisitos de Sistema](#-requisitos-de-sistema)
- [Instalação e Configuração](#-instalação-e-configuração)
  - [Central (GUI)](#central-gui)
  - [Agente (Serviço Windows)](#agente-serviço-windows)
- [Guia de Uso](#-guia-de-uso)
  - [Painel Superior – Parâmetros da Missão](#1-painel-superior--parâmetros-da-missão)
  - [Gerenciamento de Servidores](#2-gerenciamento-de-servidores)
  - [Scan de Infraestrutura](#3-scan-de-infraestrutura)
  - [Disparo de Missão (Checklist)](#4-disparo-de-missão-checklist)
  - [Deploy do Agente](#5-deploy-do-agente)
  - [Clínica de Banco de Dados](#6-clínica-de-banco-de-dados)
  - [Dashboard](#7-dashboard)
  - [Relatórios e Email](#8-relatórios-e-email)
- [Compilação](#-compilação)
  - [Compilar a Central](#compilar-a-central)
  - [Compilar o Agente (Opcional)](#compilar-o-agente-opcional)
- [Resolução de Problemas (Troubleshooting)](#-resolução-de-problemas-troubleshooting)
- [Contribuição e Suporte](#-contribuição-e-suporte)
- [Licença](#-licença)

---

## 🚀 Visão Geral

O CIGS nasceu da necessidade de automatizar e centralizar o processo de atualização de múltiplos sistemas (AC, AG, PONTO, PATRIO) em dezenas de servidores Windows. Ele é dividido em duas partes:

1. **Central (GUI)** – Aplicação desktop que funciona como “comandante”. Permite cadastrar servidores, configurar missões, disparar atualizações, visualizar dashboards e gerar relatórios.
2. **Agente (Serviço)** – Serviço Windows instalado em cada servidor alvo. Recebe ordens da Central, baixa pacotes, executa scripts e reporta status.

A comunicação entre Central e Agente é feita via API REST (HTTP), garantindo simplicidade e segurança.

---

## ✨ Funcionalidades Principais

- **Gerenciamento de servidores** – Cadastro manual, importação em massa via CSV, persistência em SQLite.
- **Scan de infraestrutura** – Verifica online/offline, versão do agente, número de clientes, latência, disco e RAM.
- **Disparo de missões** – Atualização completa (download + extração) ou apenas execução local. Suporte a múltiplos scripts (`Executa.bat`, `ExecutaOnDemand.bat`) e parâmetros.
- **Agendamento no Windows** – Cria tarefas no Task Scheduler com nomes padronizados, evitando poluição.
- **Checklist pré-disparo** – Valida URL, arquivos locais e conectividade antes de iniciar a missão.
- **Deploy remoto do agente** – Instala/atualiza o serviço CIGS_Agent em lote via rede.
- **Monitoramento em tempo real** – Dashboard com gráficos de latência e disponibilidade.
- **Clínica de banco de dados** – Executa diagnósticos e manutenção em Firebird (check, mend, sweep) e MSSQL.
- **Relatórios completos** – Geração de CSV, envio por email (com anexos) e sincronização com Google Sheets.
- **Criptografia de credenciais** – Senhas de email armazenadas com segurança usando Fernet.
- **Sanitização automática** – Corrige extrações de .rar que criam subpastas indesejadas.

---

## 🏗️ Arquitetura do Sistema
┌─────────────────┐ HTTP ┌─────────────────┐
│ CENTRAL GUI │ ────── (JSON) ───────▶ │ AGENTE (Flask)│
│ (Tkinter/ThemedTk) │ │ (Serviço Windows)│
└─────────────────┘ └─────────────────┘
│ │
│ (SQLite) │ (Task Scheduler)
┌────▼────┐ ┌────▼────┐
│ cigs_data.db │ │ Launcher.bat │
└──────────┘ └──────────┘
│
┌────▼────┐
│ Executa.bat │
└──────────┘

text

- **Central:** Armazena servidores e histórico em SQLite, comunica-se com os agentes via requests.
- **Agente:** Serviço headless (sem GUI) que expõe uma API Flask. Executa downloads, extrações e agendamentos.
- **Scripts:** O agente gera um `Launcher_{SISTEMA}.bat` que, quando executado pelo Task Scheduler, chama o script alvo (`Executa.bat` ou `ExecutaOnDemand.bat`) na raiz do sistema.

---

## 💻 Requisitos de Sistema

### Central (máquina do administrador)
- Windows 10/11 ou Windows Server 2016+
- Python 3.12 ou superior (para execução em modo script)
- Dependências Python (listadas em `requirements.txt`)
- Acesso de rede aos servidores alvo (porta 5580 aberta)

### Agente (servidores gerenciados)
- Windows Server 2008 R2 ou superior (recomendado 2012+)
- Python 3.12 ou superior (se executado como script) ou o executável compilado
- Porta 5580 liberada no firewall (para comunicação com a Central)
- Permissão de administrador para instalação como serviço

---

## 🔧 Instalação e Configuração

### Central (GUI)

#### 1. Clone ou baixe o projeto
```bash
git clone https://github.com/seu-usuario/cigs.git
cd cigs
2. Crie um ambiente virtual (recomendado)
bash
python -m venv venv
venv\Scripts\activate
3. Instale as dependências
bash
pip install -r requirements.txt
4. Configure o banco de dados
O banco SQLite (cigs_data.db) será criado automaticamente na primeira execução. Opcionalmente, você pode copiar um banco existente.

5. Execute a Central
bash
python main.py
Na primeira execução, será solicitado um token de segurança. Utilize o KeyGen.py (fornecido) para gerar a contra-senha.

6. (Opcional) Compile a Central para distribuição
Veja a seção Compilação.

Agente (Serviço Windows)
Método 1 – Instalação manual
Copie a pasta cigs_core para o servidor, em C:\CIGS\cigs_core.

Coloque os utilitários nssm.exe e UnRAR.exe em C:\CIGS.

Coloque o script Instalar_CIGS.bat em C:\CIGS.

Execute o Instalar_CIGS.bat como Administrador. Ele irá:

Verificar/parar serviços antigos

Instalar o serviço CIGS_Service usando NSSM

Configurar o firewall (porta 5580)

Iniciar o serviço

Método 2 – Deploy remoto via Central
Na Central, após cadastrar os servidores, utilize o botão 🛠️ Migrar Agente no painel de infraestrutura. A Central copiará os arquivos necessários e executará a instalação remotamente.

📖 Guia de Uso
1. Painel Superior – Parâmetros da Missão
Link (AWS/S3): URL do pacote .rar a ser baixado.

Data/Hora: Data e hora para agendamento (formato DD/MM/AAAA HH:MM).

User/Senha: Credenciais de administrador do domínio/servidor.

Sistema: Selecione AC, AG, PONTO ou PATRIO.

Script Alvo: Executa.bat (padrão) ou ExecutaOnDemand.bat.

Clientes/Args: Parâmetros adicionais para o script.

Fonte: Nuvem (download) ou Rede Local (cópia de executável).

2. Gerenciamento de Servidores
Lista TXT: Carrega IPs de um arquivo texto simples.

Importar CSV: Importa servidores em massa com template (IP;Hostname;IP_Publico;Funcao;Cliente).

Carregar DB: Recarrega a lista a partir do banco SQLite.

Novo Servidor: Cadastro manual via diálogo.

Clique direito em um servidor: Acessar RDP ou copiar IP.

3. Scan de Infraestrutura
Clique em 📡 Scanear Infra. A Central verificará todos os servidores listados, exibindo:

Status (ONLINE/OFFLINE)

Número de clientes ativos e cliente referência

Versão do agente, espaço em disco e uso de RAM (se modo full)

Latência média

Os dados são armazenados no histórico e refletidos no dashboard.

4. Disparo de Missão (Checklist)
Selecione um ou mais servidores na lista.

Clique em 🚀 DISPARAR MISSÃO (Checklist).

Uma janela de validação será aberta, verificando:

Link (se modo nuvem)

Arquivo local (se modo rede)

Conectividade com o primeiro servidor selecionado

Se tudo estiver OK, o botão AUTORIZAR DISPARO será habilitado.

Ao autorizar, a missão é agendada no Windows de cada servidor.

Dica: Use ☢️ DISPARAR EM TODOS para selecionar todos os servidores de uma vez.

5. Deploy do Agente
Clique em 🛠️ Migrar Agente no painel de infraestrutura.

A Central copiará os arquivos (CIGS_Agent.exe, nssm.exe, Instalar_CIGS.bat, UnRAR.exe) para cada servidor e executará a instalação remota via WMIC.

O progresso é mostrado na barra e no log.

6. Clínica de Banco de Dados
Selecione o motor (Firebird ou MSSQL).

Informe o caminho/nome do banco.

Escolha a operação: Check, Mend, Sweep, Backup, Restore ou Manutenção Automática.

A Central executará o comando remoto em todos os servidores selecionados (ou online).

7. Dashboard
Gráfico de Linha: Latência média dos últimos 30 scans.

Gráfico de Pizza: Disponibilidade atual (online vs offline).

Monitoramento em Tempo Real: Cartões coloridos mostrando status atual de cada servidor (atualize com o botão 🔄).

8. Relatórios e Email
Clique em 📊 Ver Relatório.

A Central coleta dados de execução de todos os servidores online e gera um CSV.

Se configurado, envia o relatório por email com estatísticas detalhadas e anexos.

Opcionalmente, sincroniza com uma planilha do Google Sheets (necessário credenciais.json).

Para configurar o email, vá em Config > Email e preencha as credenciais SMTP.

🛠️ Compilação
Compilar a Central
Use o PyInstaller para gerar um executável único:

bash
pyinstaller --noconsole --onefile --clean --noconfirm --name="CIGS_Central_3.4" --icon="assets/CIGS.ico" --collect-all ttkthemes --collect-all cryptography --collect-all matplotlib --collect-all tkcalendar --collect-all PIL --add-data "cigs_data.db;." --add-data "CIGS.key;." main.py
Arquivos que devem estar na mesma pasta do executável (ou na pasta de distribuição):

nssm.exe

UnRAR.exe

Instalar_CIGS.bat

CIGS_Agent.exe (ou a pasta cigs_core com o script e dependências)

cigs_data.db (opcional, será criado se não existir)

CIGS.key (será gerado na primeira execução)

Compilar o Agente (opcional)
Recomenda-se usar o Nuitka para gerar um executável standalone do agente, com melhor performance e ofuscação:

bash
python -m nuitka --standalone --remove-output --windows-icon-from-ico=assets/onca_pintada.ico --include-package=cigs_core --include-package=cryptography -o CIGS_Agent.exe CIGS_Agent.py
O resultado estará na pasta CIGS_Agent.dist. Copie o conteúdo para C:\CIGS nos servidores alvo.

🐛 Resolução de Problemas (Troubleshooting)
Sintoma	Causa Provável	Solução
Central não inicia	Conflito de layout (Pack vs Grid)	Verifique se todos os widgets usam apenas grid() ou apenas pack().
Agente não responde	Serviço parado ou porta bloqueada	Execute sc query CIGS_Service no servidor. Libere a porta 5580 no firewall.
Erro "Script não encontrado"	Caminho do script incorreto	Verifique se Executa.bat está na raiz do sistema (ex: C:\Atualiza\CloudUp\CloudUpCmd\AC).
Falha na autenticação de rede	Credenciais inválidas ou sem permissão	Use um usuário com privilégios administrativos no domínio/servidor.
Download falha	Link expirado ou sem acesso à internet	Teste o link no navegador. Verifique se o servidor tem acesso à internet.
Extrações criam subpastas	Sanitização não executada	Verifique se o --sanitize está sendo chamado no Launcher.bat gerado.
Email não enviado	Credenciais SMTP incorretas ou porta bloqueada	Use a função Testar na janela de configuração de email.
Dashboard sem dados	Nenhum scan realizado	Execute um scan completo primeiro.
🤝 Contribuição e Suporte
Desenvolvido por: Gabriel Levi · Fortes Tecnologia

Ano: 2026

Issues e sugestões: Abra uma issue no repositório oficial ou entre em contato com a equipe de infraestrutura.

Contribuições: Pull requests são bem-vindos! Por favor, siga as boas práticas de código e documente as alterações.

📄 Licença
Este projeto é propriedade da Fortes Tecnologia e seu uso é restrito a ambientes internos da empresa. A redistribuição ou modificação sem autorização expressa é proibida.