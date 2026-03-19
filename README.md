🚀 Visão Geral
O CIGS nasceu da necessidade de automatizar e centralizar o processo de atualização de múltiplos sistemas (AC, AG, PONTO, PATRIO) em dezenas de servidores Windows. Ele é dividido em duas partes:

Central (GUI) – Aplicação desktop que funciona como "comandante". Permite cadastrar servidores, configurar missões, disparar atualizações, visualizar dashboards e gerar relatórios.

Agente (Serviço) – Serviço Windows instalado em cada servidor alvo. Recebe ordens da Central, baixa pacotes, executa scripts e reporta status.

A comunicação entre Central e Agente é feita via API REST (HTTP), garantindo simplicidade e segurança.

✨ Funcionalidades Principais
Gerenciamento completo de servidores – Cadastro manual, importação em massa via CSV (com suporte a credenciais específicas), edição e exclusão diretamente pela interface.

Credenciais por servidor – Possibilidade de definir usuário/senha específicos para cada servidor (ideal para máquinas com contas de parceiro diferenciadas). Nas operações (RDP, deploy, missão) o sistema prioriza as credenciais específicas e, caso não existam, usa as credenciais globais do painel superior.

Scan de infraestrutura – Verifica online/offline, versão do agente, número de clientes, latência, disco e RAM.

Disparo de missões – Atualização completa (download + extração) ou apenas execução local. Suporte a múltiplos scripts (Executa.bat, ExecutaOnDemand.bat) e parâmetros.

Agendamento no Windows – Cria tarefas no Task Scheduler com nomes padronizados, evitando poluição.

Checklist pré-disparo – Valida URL, arquivos locais e conectividade antes de iniciar a missão.

Deploy remoto do agente – Instala/atualiza o serviço CIGS_Agent em lote via rede, agora utilizando as credenciais específicas de cada servidor.

Monitoramento em tempo real – Dashboard com gráficos de latência e disponibilidade, além de cartões de status coloridos.

Clínica de banco de dados – Executa diagnósticos e manutenção em Firebird (check, mend, sweep, backup, restore, automático) e MSSQL (checkdb, manutenção completa).

Varredura de bancos de dados – Localiza automaticamente arquivos .FDB nos servidores (compartilhamentos administrativos), usando as credenciais adequadas.

Gerador WAR – Cria múltiplos arquivos .war a partir de uma base e uma lista de nomes.

Relatórios completos – Geração de CSV, envio por email (com anexos) e sincronização com Google Sheets.

Criptografia de credenciais – Senhas de email armazenadas com segurança usando Fernet; senha mestra para acesso ao sistema (bcrypt + Fernet).

Sanitização automática – Corrige extrações de .rar que criam subpastas indesejadas.

🏗️ Arquitetura do Sistema
text
┌─────────────────┐    HTTP    ┌─────────────────┐
│   CENTRAL GUI   │ ──────────▶ │ AGENTE (Flask)  │
│ (Tkinter/Themed)│  (JSON)     │(Serviço Windows)│
└─────────────────┘             └─────────────────┘
         │                              │
         │ (PostgreSQL)                  │ (Task Scheduler)
    ┌────▼────┐                    ┌────▼────┐
    │   cigs_db │                    │Launcher.bat│
    └──────────┘                    └──────────┘
                                            │
                                      ┌────▼────┐
                                      │Executa.bat│
                                      └──────────┘
Central: Gerencia a interface e toda a lógica de negócio. Conecta-se ao PostgreSQL para armazenar servidores, histórico e configurações.

Banco de Dados (PostgreSQL): Centraliza os dados de forma segura e performática, permitindo acesso concorrente.

Agente: Serviço headless (sem GUI) que expõe uma API Flask. Executa downloads, extrações e agendamentos nos servidores alvo.

Scripts: O agente gera um Launcher_{SISTEMA}.bat que, quando executado pelo Task Scheduler, chama o script alvo (Executa.bat ou ExecutaOnDemand.bat) na raiz do sistema.

💻 Requisitos de Sistema
Central (máquina do administrador)
Windows 10/11 ou Windows Server 2016+

Python 3.12 ou superior (para execução em modo script)

Dependências Python (listadas em requirements.txt)

Acesso de rede aos servidores alvo (porta 5580 aberta)

Acesso de rede ao servidor de Banco de Dados PostgreSQL (porta padrão 5432)

Banco de Dados (PostgreSQL)
Um servidor ou instância PostgreSQL 12+ acessível pela rede.

Um banco de dados criado para o CIGS (ex: cigs_db).

Um usuário com privilégios de leitura/escrita nesse banco.

Agente (servidores gerenciados)
Windows Server 2008 R2 ou superior (recomendado 2012+)

Python 3.12 ou superior (se executado como script) ou o executável compilado

Porta 5580 liberada no firewall (para comunicação com a Central)

Permissão de administrador para instalação como serviço

🔧 Instalação e Configuração
1. Configurar o Banco de Dados (PostgreSQL)
Antes de executar a Central, é necessário preparar o banco de dados:

Certifique-se de ter um servidor PostgreSQL em execução e acessível.

Crie um banco de dados para o CIGS:

sql
CREATE DATABASE cigs_db;
Crie um usuário e conceda privilégios:

sql
CREATE USER cigs_user WITH PASSWORD 'sua_senha_forte';
GRANT ALL PRIVILEGES ON DATABASE cigs_db TO cigs_user;
2. Central (GUI)
Clone ou baixe o projeto
bash
git clone https://github.com/Biellima2811/CIGS.git
cd CIGS
Crie um ambiente virtual (recomendado)
bash
python -m venv venv
venv\Scripts\activate
Instale as dependências
bash
pip install -r requirements.txt
Nota: O requirements.txt foi atualizado para incluir o psycopg2-binary (driver do PostgreSQL).

Configure a conexão com o banco de dados
Na primeira execução, a Central solicitará as configurações de conexão com o PostgreSQL:

Host: Endereço do servidor PostgreSQL (ex: localhost ou 192.168.1.100)

Porta: Geralmente 5432

Nome do Banco: O nome que você criou (ex: cigs_db)

Usuário: cigs_user

Senha: A senha definida para o usuário

Essas configurações serão salvas em um arquivo config.ini para uso futuro. O sistema criará automaticamente as tabelas necessárias ao conectar.

Execute a Central
bash
python main.py
Na primeira execução, será solicitada a criação de uma senha mestra. Utilize-a para acessar o sistema posteriormente.

(Opcional) Compile a Central para distribuição
Veja a seção Compilação.

3. Agente (Serviço Windows)
O processo de instalação do agente nos servidores gerenciados não se altera com a migração do banco de dados. Utilize os mesmos métodos:

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
Na Central, após cadastrar os servidores, utilize o botão 🛠️ Migrar Agente no painel de infraestrutura. A Central copiará os arquivos necessários e executará a instalação remotamente, utilizando as credenciais específicas de cada servidor (ou as globais, se não houver específicas).

📖 Guia de Uso
1. Painel Superior – Parâmetros da Missão
Link (AWS/S3): URL do pacote .rar a ser baixado.

Data/Hora: Data e hora para agendamento (formato DD/MM/AAAA HH:MM).

User/Senha: Credenciais de administrador do domínio/servidor (serão usadas como fallback caso o servidor não tenha credenciais próprias).

Sistema: Selecione AC, AG, PONTO ou PATRIO.

Script Alvo: Executa.bat (padrão) ou ExecutaOnDemand.bat.

Clientes/Args: Parâmetros adicionais para o script.

Fonte: Nuvem (download) ou Rede Local (cópia de executável).

2. Gerenciamento de Servidores
Lista TXT: Carrega IPs de um arquivo texto simples.

Importar CSV: Importa servidores em massa. O template inclui as colunas UsuarioEspecifico e SenhaEspecifica. Exemplo:

text
IP;Hostname;IP_Publico;Funcao;Cliente;UsuarioEspecifico;SenhaEspecifica
192.168.1.50;SRV-APP01;200.1.1.50;APP;Cliente Exemplo;;
192.168.1.51;SRV-BD01;200.1.1.51;BD;Cliente Exemplo;fortes\admin;senha123
Carregar DB: Recarrega a lista a partir do banco PostgreSQL.

Novo Servidor: Cadastro manual, com campos opcionais para usuário/senha específicos.

Clique direito em um servidor: Menu com opções:

Acessar RDP (usa credenciais específicas se disponíveis)

Copiar IP

Editar Servidor (altera todos os dados, inclusive credenciais)

Excluir Servidor (remove do banco)

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

Ao autorizar, a missão é agendada no Windows de cada servidor (as credenciais específicas de cada um são respeitadas).

Dica: Use ☢️ DISPARAR EM TODOS para selecionar todos os servidores de uma vez.

5. Deploy do Agente
Clique em 🛠️ Migrar Agente no painel de infraestrutura. A Central copiará os arquivos (CIGS_Agent.exe, nssm.exe, Instalar_CIGS.bat, UnRAR.exe) para cada servidor e executará a instalação remota via WMIC, utilizando as credenciais específicas de cada servidor (fallback para as globais). O progresso é mostrado na barra e no log.

6. Clínica de Banco de Dados
Selecione o motor (Firebird ou MSSQL).

Informe o caminho/nome do banco (ou utilize o botão 🔍 Scan para localizar bancos no servidor selecionado).

Escolha a operação: Check, Mend, Sweep, Backup, Restore, Manutenção Automática (Firebird) ou CheckDB/Manutenção Completa (MSSQL).

A Central executará o comando remoto em todos os servidores selecionados (ou online).

7. Dashboard
Gráfico de Linha: Latência média dos últimos 30 scans.

Gráfico de Pizza: Disponibilidade atual (online vs offline).

Monitoramento em Tempo Real: Cartões coloridos mostrando status atual de cada servidor (atualize com o botão 🔄). As credenciais específicas são usadas para a consulta de status.

8. Gerador WAR
Selecione um arquivo de nomes (.txt, um nome por linha), um arquivo base .war e uma pasta de destino. Clique em Gerar Cópias para criar múltiplos arquivos .war (cada um com o nome da lista).

9. Relatórios e Email
Clique em 📊 Ver Relatório. A Central coleta dados de execução de todos os servidores online e gera um CSV. Se configurado, envia o relatório por email com estatísticas detalhadas e anexos (CSV e log). Opcionalmente, sincroniza com uma planilha do Google Sheets (necessário credenciais.json). Para configurar o email, vá em Config > Email e preencha as credenciais SMTP.

🛠️ Compilação
Compilar a Central
Use o PyInstaller para gerar um executável único (com suporte ao PostgreSQL):

bash
pyinstaller --noconsole --onefile --clean --noconfirm --noupx --name="CIGS_Central_v3.7.3.2" --icon="assets/CIGS.ico" --collect-all ttkthemes --collect-all cryptography --collect-all matplotlib --collect-all tkcalendar --collect-all PIL --collect-all psycopg2 main.py
Arquivos que devem estar na mesma pasta do executável (ou na pasta de distribuição):

nssm.exe

UnRAR.exe

Instalar_CIGS.bat

CIGS_Agent.exe (ou a pasta cigs_core com o script e dependências)

config.ini (será gerado na primeira execução)

CIGS.key (será gerado na primeira execução)

credenciais.json (para integração com Google Sheets, opcional)

Compilar o Agente (opcional)
Recomenda-se usar o Nuitka para gerar um executável standalone do agente, com melhor performance e ofuscação:

bash
python -m nuitka --standalone --remove-output --windows-icon-from-ico=assets/onca_pintada.ico --include-package=cigs_core --include-package=cryptography -o CIGS_Agent.exe CIGS_Agent.py
O resultado estará na pasta CIGS_Agent.dist. Copie o conteúdo para C:\CIGS nos servidores alvo.

🐛 Resolução de Problemas (Troubleshooting)
Sintoma	Causa Provável	Solução
Erro de conexão com o banco na inicialização	Configurações do PostgreSQL incorretas ou servidor inacessível	Verifique o arquivo config.ini. Teste a conexão usando um cliente como pgAdmin ou psql.
Central não inicia	Conflito de layout (Pack vs Grid)	Verifique se todos os widgets usam apenas grid() ou apenas pack().
Agente não responde	Serviço parado ou porta bloqueada	Execute sc query CIGS_Service no servidor. Libere a porta 5580 no firewall.
Erro "Script não encontrado"	Caminho do script incorreto	Verifique se Executa.bat está na raiz do sistema (ex: C:\Atualiza\CloudUp\CloudUpCmd\AC).
Falha na autenticação de rede	Credenciais inválidas ou sem permissão	Use um usuário com privilégios administrativos no domínio/servidor. Verifique as credenciais específicas do servidor.
Download falha	Link expirado ou sem acesso à internet	Teste o link no navegador. Verifique se o servidor tem acesso à internet.
Extrações criam subpastas	Sanitização não executada	Verifique se o --sanitize está sendo chamado no Launcher.bat gerado.
Email não enviado	Credenciais SMTP incorretas ou porta bloqueada	Use a função Testar na janela de configuração de email.
Dashboard sem dados	Nenhum scan realizado	Execute um scan completo primeiro.
Servidor com credenciais próprias não usa‑as	Lógica não implementada na operação	Verifique se a função obter_credenciais_servidor(ip) está sendo chamada na rotina (ex: no worker_deploy, worker_disparo, etc.). Todas as operações principais já foram adaptadas.
Falha ao compilar com PyInstaller (psycopg2)	O driver não foi incluído no executável	Use a flag --collect-all psycopg2 no comando do PyInstaller.
🤝 Contribuição e Suporte
Desenvolvido por: Gabriel Levi · Fortes Tecnologia
Ano: 2026
Versão Atual: 3.7.3.2

Issues e sugestões: Abra uma issue no repositório oficial ou entre em contato com a equipe de infraestrutura.

Contribuições: Pull requests são bem-vindos! Por favor, siga as boas práticas de código e documente as alterações.

⚖️ Licença
Este projeto é proprietário e de uso interno da Fortes Tecnologia.
