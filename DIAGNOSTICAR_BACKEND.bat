@echo off
echo ========================================
echo DIAGNOSTICAR BACKEND
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

REM Executar diagnóstico
echo Executando diagnostico do backend...
echo.
python backend\scripts\diagnosticar_backend.py

echo.
pause

