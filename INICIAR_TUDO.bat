@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 INICIANDO PROJETO COMPLETO
echo ============================================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

echo 📋 Verificando servidores...
echo.

REM Verificar backend
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend não está rodando. Iniciando...
    start "Backend - Comex Analyzer" cmd /k "INICIAR_BACKEND_FACIL.bat"
    echo ✅ Backend iniciando em nova janela...
    timeout /t 3 /nobreak >nul
) else (
    echo ✅ Backend já está rodando na porta 8000
)
echo.

REM Verificar frontend
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend não está rodando. Iniciando...
    start "Frontend - Comex Analyzer" cmd /k "INICIAR_FRONTEND.bat"
    echo ✅ Frontend iniciando em nova janela...
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Frontend já está rodando na porta 3000
)
echo.

echo ============================================================
echo ✅ SERVIDORES INICIADOS
echo ============================================================
echo.
echo 📍 URLs:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    Docs API: http://localhost:8000/docs
echo.
echo ⚠️  Mantenha as janelas abertas!
echo ⚠️  Para parar, feche as janelas ou pressione CTRL+C em cada uma
echo.
echo Aguardando 5 segundos antes de abrir o navegador...
timeout /t 5 /nobreak >nul

REM Tentar abrir o navegador
start http://localhost:3000

echo.
echo ✅ Navegador aberto!
echo.
pause
