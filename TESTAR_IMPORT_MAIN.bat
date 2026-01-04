@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 TESTANDO IMPORTAÇÃO DO MAIN.PY
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

echo Testando import do main.py...
python -c "import sys; sys.path.insert(0, '.'); import main; print('✅ Import OK!')"

if errorlevel 1 (
    echo.
    echo ❌ Erro ao importar main.py!
    echo.
    echo Executando diagnóstico detalhado...
    python -c "import sys; sys.path.insert(0, '.'); import main"
    echo.
) else (
    echo.
    echo ✅ main.py pode ser importado sem erros!
)

echo.
pause

