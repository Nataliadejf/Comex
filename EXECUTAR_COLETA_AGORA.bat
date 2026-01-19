@echo off
echo ========================================
echo EXECUTAR COLETA DE DADOS - RENDER
echo ========================================
echo.
echo Backend detectado como funcionando!
echo Executando coleta agora...
echo.

cd /d "%~dp0"

REM Executar coleta diretamente
python backend\scripts\executar_coleta.py --meses 24

echo.
echo ========================================
echo COLETA CONCLUIDA
echo ========================================
echo.
echo Para avaliar o metodo usado, execute:
echo   AVALIAR_METODO.bat
echo.
pause



