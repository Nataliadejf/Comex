@echo off
echo ============================================================
echo POPULANDO BANCO DE DADOS COM DADOS REALISTAS
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo 🚀 Executando script de popular banco...
    echo.
    python scripts\popular_banco_rapido.py
    echo.
    pause
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: python -m venv venv
    pause
)


