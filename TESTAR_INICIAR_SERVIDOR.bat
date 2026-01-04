@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 TESTANDO INÍCIO DO SERVIDOR
echo ============================================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

if not exist "backend" (
    echo ❌ ERRO: Pasta 'backend' não encontrada!
    pause
    exit /b 1
)

cd backend

REM Ativar ambiente virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo ✅ Ambiente virtual ativado
echo.

echo Testando import do main.py...
python -c "from main import app; print('✅ Import OK')" 2>&1
if errorlevel 1 (
    echo ❌ ERRO ao importar!
    pause
    exit /b 1
)
echo.

echo Parando processos na porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo    Encerrando processo %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo 🚀 INICIANDO SERVIDOR...
echo ============================================================
echo.
echo ⚠️  Mantenha esta janela aberta!
echo ⚠️  Para parar, pressione CTRL+C
echo.
echo 📍 Acesse: http://localhost:8000/docs
echo.
echo ============================================================
echo.

REM Tentar iniciar o servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo ❌ ERRO ao iniciar servidor!
    echo.
    echo Verifique os erros acima.
    echo.
    pause
)

