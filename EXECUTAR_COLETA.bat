@echo off
echo ========================================
echo EXECUTAR COLETA DE DADOS
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python e tente novamente.
    pause
    exit /b 1
)

REM Executar script de coleta
echo Executando coleta de dados...
echo.
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

