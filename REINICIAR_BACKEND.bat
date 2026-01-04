@echo off
echo ============================================================
echo REINICIANDO BACKEND - COMEX ANALYZER
echo ============================================================
echo.

cd /d "%~dp0backend"

echo Parando processos na porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Encerrando processo %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

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



