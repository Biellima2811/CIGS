🚀 CIGS – Central Integrada de Gerenciamento de Sistemas

Versão 3.7.3.2 (Estável)

O CIGS é uma plataforma de orquestração tática para gerenciamento em massa de servidores Windows.
Permite atualizações remotas, monitoramento de saúde, execução de scripts, geração de relatórios e automações operacionais — tudo através de uma interface gráfica intuitiva e uma arquitetura cliente-servidor robusta.

🆕 Novidades da versão

⚡ Melhoria de performance
Otimizações significativas nas rotinas de scan e execução de missões.

🗄️ Migração para PostgreSQL
Substituição do SQLite por PostgreSQL, trazendo:

Maior robustez

Suporte a concorrência

Melhor segurança para múltiplos administradores

📌 Índice

Visão Geral

Funcionalidades

Arquitetura

Requisitos

Instalação

Guia de Uso

Compilação

Troubleshooting

Contribuição

Licença

🚀 Visão Geral

O CIGS foi desenvolvido para automatizar e centralizar atualizações de sistemas corporativos (AC, AG, PONTO, PATRIO) em múltiplos servidores.

🔹 Componentes

Central (GUI)
Aplicação desktop responsável por:

Gerenciar servidores

Configurar missões

Monitorar execução

Gerar relatórios

Agente (Serviço Windows)
Executado nos servidores alvo:

Recebe comandos da central

Executa scripts

Realiza downloads

Retorna status

📡 Comunicação via API REST (HTTP)

✨ Funcionalidades Principais

📋 Gerenciamento completo de servidores (manual ou CSV)

🔐 Credenciais por servidor com fallback global

📡 Scan de infraestrutura (status, latência, recursos)

🚀 Execução de missões em lote

⏰ Agendamento via Task Scheduler

✅ Checklist pré-execução

🛠️ Deploy remoto do agente

📊 Dashboard em tempo real

🧪 Clínica de banco de dados:

Firebird (check, mend, sweep, backup, restore)

MSSQL (checkdb e manutenção)

🔍 Varredura automática de bancos (.FDB)

📦 Gerador de arquivos .war

📄 Relatórios (CSV + e-mail + Google Sheets)

🔒 Criptografia de credenciais (Fernet + bcrypt)

🧹 Sanitização automática de extrações .rar

🏗️ Arquitetura do Sistema

Central

Interface + lógica de negócio

Comunicação com PostgreSQL

PostgreSQL

Armazenamento centralizado

Suporte a múltiplos usuários

Agente

Serviço Windows (Flask API)

Execução de tarefas locais

Scripts

Execução via Launcher_{SISTEMA}.bat

💻 Requisitos de Sistema
🖥️ Central

Windows 10/11 ou Server 2016+

Python 3.12+

Acesso à rede (porta 5580)

Acesso ao PostgreSQL (porta 5432)

🗄️ Banco de Dados

PostgreSQL 12+

Banco criado (ex: cigs_db)

Usuário com permissão total

⚙️ Agente

Windows Server 2008 R2+ (ideal: 2012+)

Porta 5580 liberada

Permissão de administrador

🔧 Instalação e Configuração
1. Banco de Dados
CREATE DATABASE cigs_db;

CREATE USER cigs_user WITH PASSWORD 'sua_senha_forte';
GRANT ALL PRIVILEGES ON DATABASE cigs_db TO cigs_user;
2. Central (GUI)
git clone https://github.com/Biellima2811/CIGS.git
cd CIGS

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

Na primeira execução:

Configure o PostgreSQL

Defina a senha mestra

python main.py
3. Agente

Opções:

Instalação manual (Instalar_CIGS.bat)

Deploy remoto via Central

📖 Guia de Uso
🔹 Painel Superior

Configuração de missões (URL, data, script, credenciais)

🔹 Gerenciamento de Servidores

Cadastro, edição e importação via CSV

🔹 Scan de Infraestrutura

Verifica status e recursos

🔹 Disparo de Missões

Execução com checklist automático

🔹 Deploy do Agente

Instalação remota

🔹 Clínica de Banco

Manutenção Firebird e MSSQL

🔹 Dashboard

Monitoramento em tempo real

🔹 Relatórios

Exportação e envio automático

🛠️ Compilação
Central (PyInstaller)
pyinstaller --noconsole --onefile --clean --noconfirm --noupx \
--name="CIGS_Central_v3.8.0" \
--icon="assets/CIGS.ico" \
--collect-all ttkthemes \
--collect-all cryptography \
--collect-all matplotlib \
--collect-all tkcalendar \
--collect-all PIL \
--collect-all psycopg2 \
main.py
Agente (Nuitka)
python -m nuitka --standalone --remove-output \
--windows-icon-from-ico=assets/onca_pintada.ico \
--include-package=cigs_core \
--include-package=cryptography \
-o CIGS_Agent.exe CIGS_Agent.py
🐛 Resolução de Problemas
Problema	Causa	Solução
Erro no banco	Config incorreta	Verificar config.ini
Scan lento	Falta de índice	Revisar banco
Erro PyInstaller	psycopg2 ausente	Usar --collect-all
Agente offline	Porta bloqueada	Liberar 5580
Credenciais não usadas	Falha lógica	Revisar função
🤝 Contribuição e Suporte

Autor: Gabriel Levi

Empresa: Fortes Tecnologia

Ano: 2026

💡 Sugestões e melhorias: abra uma issue
🔧 Pull requests são bem-vindos

⚖️ Licença

Projeto proprietário de uso interno da Fortes Tecnologia.
