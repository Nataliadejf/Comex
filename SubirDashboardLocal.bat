@echo off
chcp 65001 >nul
set PROJETO=%~dp0
set BACKEND=%PROJETO%backend
set FRONTEND=%PROJETO%frontend

echo.
echo ============================================================
echo   DASHBOARD LOCAL - Abrindo Backend e Frontend
echo ============================================================
echo.

if not exist "%BACKEND%\run.py" (
    echo ERRO: backend\run.py nao encontrado.
    pause
    exit /b 1
)
if not exist "%FRONTEND%\package.json" (
    echo ERRO: frontend\package.json nao encontrado.
    pause
    exit /b 1
)

echo [1/2] Abrindo BACKEND (porta 8000) em nova janela...
start "Comex Backend" cmd /k "cd /d "%BACKEND%" && set PORT=8000 && python run.py"
echo       Aguarde alguns segundos ate aparecer "Uvicorn running" na janela do backend.
echo.

echo [2/2] Abrindo FRONTEND (porta 3000) em nova janela...
start "Comex Frontend" cmd /k "cd /d "%FRONTEND%" && npm start"

echo.
echo Quando o frontend abrir o navegador, acesse:
echo    http://localhost:3000/dashboard
echo.
echo Se abrir o Electron e der "Connection Failed", espere 1-2 minutos
echo e clique em "Restart Browser" ou feche e abra de novo.
echo.
pause
