@echo off
echo ============================================================
echo INICIANDO BACKEND - COMEX ANALYZER
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo 🚀 Iniciando servidor na porta 8000...
    echo.
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: python -m venv venv
    pause
)



