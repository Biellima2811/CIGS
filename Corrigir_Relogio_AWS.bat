@echo off
color 0A
echo ===================================================
echo     C.I.G.S - SINCRONIZADOR DE RELOGIO (NTP)
echo ===================================================
echo.

echo [1/6] Parando o servico de tempo do Windows...
net stop w32time
echo.

echo [2/6] Limpando registros antigos e bugs...
w32tm /unregister
w32tm /register
echo.

echo [3/6] Iniciando o servico novamente...
net start w32time
echo.

echo [4/6] Apontando para servidores globais (pool.ntp.org)...
w32tm /config /syncfromflags:manual /manualpeerlist:"pool.ntp.org time.windows.com"
echo.

echo [5/6] Aplicando a nova configuracao...
w32tm /config /update
echo.

echo [6/6] Forcando a sincronizacao IMEDIATA...
w32tm /resync
echo.

echo ===================================================
echo MISSAO CONCLUIDA! O relogio foi sincronizado.
echo ===================================================
pause