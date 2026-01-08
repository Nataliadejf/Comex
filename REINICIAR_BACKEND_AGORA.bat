@echo off
echo ========================================
echo Reiniciando Backend Comex Analyzer
echo ========================================
echo.

cd /d "%~dp0"

echo Parando processos existentes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *main:app*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Iniciando backend...
cd backend
if exist "venv\Scripts\python.exe" (
    start "Comex Backend" "venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
) else (
    start "Comex Backend" python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
)

echo.
echo Backend iniciado!
echo Aguarde alguns segundos para o servidor iniciar completamente...
echo.
echo Teste acessando: http://localhost:8000/health
echo.
pause



