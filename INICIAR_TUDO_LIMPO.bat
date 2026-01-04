@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 INICIANDO BACKEND E FRONTEND (LIMPO)
echo ============================================================
echo.

REM Parar processos existentes
echo Parando processos existentes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo 1️⃣  INICIANDO BACKEND...
echo ============================================================
echo.

start "Backend - Comex Analyzer" cmd /k "cd /d %~dp0backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) else (echo ❌ Ambiente virtual não encontrado! && pause)"

timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo 2️⃣  INICIANDO FRONTEND...
echo ============================================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo ⚠️  node_modules não encontrado. Instalando dependências...
    call npm install
)

start "Frontend - Comex Analyzer" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ============================================================
echo ✅ SERVIDORES INICIADOS!
echo ============================================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul

