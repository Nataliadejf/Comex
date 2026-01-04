@echo off
chcp 65001 >nul
echo ============================================================
echo 🔄 REINICIANDO TUDO (BACKEND + FRONTEND)
echo ============================================================
echo.

cd /d "%~dp0"

REM Parar tudo primeiro
echo 1️⃣ Parando processos existentes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Parando processo backend (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo Parando processo frontend (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 3 /nobreak >nul

echo.
echo 2️⃣ Iniciando Backend...
echo.
start "Backend - Comex Analyzer" cmd /k "cd /d %~dp0backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat && echo ✅ Ambiente virtual ativado && echo. && echo Aguarde alguns segundos... && timeout /t 2 /nobreak >nul && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) else (echo ❌ Ambiente virtual não encontrado! && pause)"

echo Aguardando backend inicializar...
timeout /t 8 /nobreak >nul

echo.
echo 3️⃣ Verificando se backend está respondendo...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Backend ainda não está respondendo, aguarde mais alguns segundos...
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Backend está respondendo!
)

echo.
echo 4️⃣ Iniciando Frontend...
echo.
cd /d "%~dp0frontend"

REM Garantir que .env existe
if not exist ".env" (
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=http://localhost:8000 > .env
)

if not exist "node_modules" (
    echo ⚠️ node_modules não encontrado. Instalando dependências...
    call npm install
)

start "Frontend - Comex Analyzer" cmd /k "cd /d %~dp0frontend && echo ✅ Frontend iniciando... && echo. && echo Aguarde alguns segundos para o React compilar... && echo. && npm start"

echo.
echo ============================================================
echo ✅ REINICIAÇÃO CONCLUÍDA!
echo ============================================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Aguarde alguns segundos para ambos inicializarem completamente.
echo Depois, recarregue a página do navegador (Ctrl+F5).
echo.
pause

