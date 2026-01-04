@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 ADICIONANDO CAMPO nome_empresa AO BANCO
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

python scripts\adicionar_campo_nome_empresa.py

pause

