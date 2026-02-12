@echo off
setlocal
title Instalador Tatico CIGS v3.0


:: ==========================================
:: 1. VERIFICAÇÃO DE ADMINISTRADOR
:: ==========================================
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Permissoes de Admin confirmadas.
) else (
    echo [ERRO] Este script precisa ser executado como ADMINISTRADOR.
    echo Clique com o botao direito e selecione "Executar como Administrador".
    pause
    exit
)

:: ==========================================
:: 2. DEFINIÇÃO DE AMBIENTE
:: ==========================================
:: Define a pasta C:\CIGS como raiz fixa para evitar erros
set "ROOT_DIR=C:\CIGS"
set "EXE_PATH=%ROOT_DIR%\CIGS_Agent.dist\CIGS_Agent.exe"
set "NSSM=%ROOT_DIR%\nssm.exe"

echo.
echo --- PREPARANDO TERRENO EM %ROOT_DIR% ---
if not exist "%ROOT_DIR%" (
    echo [ERRO] A pasta %ROOT_DIR% nao existe! Crie a pasta e coloque os arquivos la.
    pause
    exit
)

cd /d "%ROOT_DIR%"

:: Verifica se o executável existe (tenta na raiz ou na pasta dist)
if not exist "%EXE_PATH%" (
    if exist "%ROOT_DIR%\CIGS_Agent.exe" (
        set "EXE_PATH=%ROOT_DIR%\CIGS_Agent.exe"
    ) else (
        echo [ERRO] Nao encontrei o CIGS_Agent.exe!
        echo Verifique se ele esta em %ROOT_DIR% ou %ROOT_DIR%\CIGS_Agent.dist
        pause
        exit
    )
)

echo [OK] Executavel encontrado: %EXE_PATH%

:: ==========================================
:: 3. LIMPEZA DA ÁREA (MATAR VERSÕES ANTIGAS)
:: ==========================================
echo.
echo --- PARANDO SERVICOS ANTIGOS ---
sc stop CIGS_Service >nul 2>&1
sc delete CIGS_Service >nul 2>&1
taskkill /f /im CIGS_Agent.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Area limpa.

:: ==========================================
:: 4. INSTALAÇÃO DO SERVIÇO (NSSM)
:: ==========================================
echo.
echo --- INSTALANDO NOVO SERVICO ---

:: Instala o serviço
"%NSSM%" install CIGS_Service "%EXE_PATH%"
if %errorLevel% neq 0 (
    echo [ERRO] Falha ao instalar servico. O nssm.exe esta na pasta?
    pause
    exit
)

:: Configura diretório de trabalho (CRUCIAL)
"%NSSM%" set CIGS_Service AppDirectory "%ROOT_DIR%"

:: Configura reinício automático em caso de falha
"%NSSM%" set CIGS_Service AppExit Default Restart

echo [OK] Servico configurado.

:: ==========================================
:: 5. LIBERAÇÃO DE FIREWALL (NETSH)
:: ==========================================
echo.
echo --- CONFIGURANDO FIREWALL ---
:: No arquivo Instalar_CIGS.bat
netsh advfirewall firewall delete rule name="CIGS_Porta_5578" >nul 2>&1
:: Mude o nome e a porta abaixo
netsh advfirewall firewall add rule name="CIGS_Porta_5580" dir=in action=allow protocol=TCP localport=5580 profile=any
echo [OK] Porta 5580 liberada (TCP).

:: ==========================================
:: 6. INICIALIZAÇÃO
:: ==========================================
echo.
echo --- INICIANDO AGENTE ---
sc start CIGS_Service

echo.
echo ==========================================
echo      INSTALACAO CONCLUIDA COM SUCESSO
echo ==========================================
echo.
echo Teste o acesso agora: http://localhost:5578/cigs/status
echo.
