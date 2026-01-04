@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 TESTE RÁPIDO DO BACKEND
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo.
echo Testando import do main.py...
python -c "from main import app; print('✅ Import OK')" 2>&1
if errorlevel 1 (
    echo ❌ ERRO ao importar!
    echo.
    echo Executando diagnóstico...
    python -c "import sys; sys.path.insert(0, '.'); from main import app" 2>&1
    pause
    exit /b 1
)

echo.
echo ✅ Tudo OK! Backend pronto para iniciar.
echo.
pause

