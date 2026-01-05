@echo off
echo ========================================
echo AVALIAR METODO DE COLETA
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

REM Executar script de avaliação
echo Avaliando metodo usado na coleta...
echo.
python backend\scripts\avaliar_metodo.py

echo.
pause

