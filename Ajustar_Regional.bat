@echo off
:: C.I.G.S - Script de Padronização Regional
:: Força o formato de data DD/MM/AAAA e hora HH:mm

echo [!] Iniciando padronização regional...

:: Ajusta a data curta para DD/MM/AAAA
reg add "HKCU\Control Panel\International" /v sShortDate /t REG_SZ /d dd/MM/yyyy /f

:: Ajusta o separador de data para /
reg add "HKCU\Control Panel\International" /v sDate /t REG_SZ /d / /f

:: Ajusta o formato de hora para 24h (HH:mm)
reg add "HKCU\Control Panel\International" /v sShortTime /t REG_SZ /d HH:mm /f
reg add "HKCU\Control Panel\International" /v sTimeFormat /t REG_SZ /d HH:mm:ss /f

echo [OK] Formato de data e hora ajustado com sucesso.
echo [!] Nota: Em alguns casos, o agendador de tarefas exige logoff para aplicar 100%%.

pause