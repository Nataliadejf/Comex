@echo off
echo ========================================
echo   PARANDO BACKEND E FRONTEND
echo ========================================
echo.

echo Parando todos os processos...
taskkill /F /IM node.exe 2>nul
if %errorlevel% == 0 (
    echo Frontend parado!
) else (
    echo Nenhum processo do frontend encontrado.
)

taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo Backend parado!
) else (
    echo Nenhum processo do backend encontrado.
)

taskkill /F /IM uvicorn.exe 2>nul

echo.
echo Aguardando processos finalizarem...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   TODOS OS PROCESSOS FORAM PARADOS
echo ========================================
echo.
pause





