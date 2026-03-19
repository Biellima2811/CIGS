@echo off
color 0A
title CIGS - Agendador Manual Offline
echo ===================================================
echo      C.I.G.S - AGENDADOR TATICO MANUAL (OFFLINE)
echo ===================================================
echo.

set /p data_exec="[1/3] Digite a DATA da missao (Ex: 15/03/2026): "
set /p hora_exec="[2/3] Digite a HORA da missao (Ex: 23:30): "

echo.
echo [3/3] Escolha o SISTEMA ALVO para agendamento:
echo 1 - AC     (C:\Atualiza\CloudUp\CloudUpCmd\AC\Executa.Bat)
echo 2 - Ponto  (C:\Atualiza\CloudUp\CloudUpCmd\Ponto\Executa.Bat)
echo 3 - Patrio (C:\Atualiza\CloudUp\CloudUpCmd\Patrio\Executa.Bat)
echo.
set /p opcao="Digite a opcao (1, 2 ou 3): "

:: Define o caminho de acordo com a escolha
if "%opcao%"=="1" (
    set "CAMINHO_ALVO=C:\Atualiza\CloudUp\CloudUpCmd\AC\Executa.Bat"
) else if "%opcao%"=="2" (
    set "CAMINHO_ALVO=C:\Atualiza\CloudUp\CloudUpCmd\Ponto\Executa.Bat"
) else if "%opcao%"=="3" (
    set "CAMINHO_ALVO=C:\Atualiza\CloudUp\CloudUpCmd\Patrio\Executa.Bat"
) else (
    color 0C
    echo.
    echo [!] ERRO: Opcao invalida. Operacao abortada.
    pause
    exit /b
)

:: Trava de Seguranca: Verifica se o arquivo realmente existe no servidor
if not exist "%CAMINHO_ALVO%" (
    echo.
    color 0C
    echo [!] ERRO TATICO: O arquivo NAO FOI ENCONTRADO neste servidor!
    echo Caminho procurado: "%CAMINHO_ALVO%"
    echo Verifique se a pasta esta correta e tente novamente.
    pause
    exit /b
)

:: Formata o caminho completo com aspas para o schtasks
set CAMINHO_COMPLETO="%CAMINHO_ALVO%"

color 0A
echo.
echo ===================================================
echo [!] REVISAO DO PLANO TATICO:
echo Data: %data_exec%
echo Hora: %hora_exec%
echo Alvo: %CAMINHO_COMPLETO%
echo ===================================================
echo Pressione qualquer tecla para armar o Agendador...
pause >nul

:: O comando de agendamento (Privilegios maximos, roda 1 vez, forca sobrescrita)
schtasks /create /tn "CIGS_Operacao_Manual" /tr %CAMINHO_COMPLETO% /sc once /st %hora_exec% /sd %data_exec% /rl highest /f

echo.
if %errorlevel% equ 0 (
    echo [VITORIA] Missao cravada no Agendador de Tarefas do Windows!
) else (
    color 0C
    echo [ALERTA] Falha ao agendar! Voce lembrou de executar como ADMINISTRADOR?
)
echo.
pause