@echo off
chcp 65001 >nul
echo ============================================================
echo 📝 POPULANDO CAMPO nome_empresa
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

python scripts\popular_nome_empresa.py

echo.
pause

