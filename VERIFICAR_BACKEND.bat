@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo VERIFICANDO STATUS DO BACKEND
echo ============================================================
echo.

REM Verificar se há processo na porta 8000
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ❌ Nenhum processo encontrado na porta 8000
    echo.
    echo O backend não está rodando!
    echo Execute: INICIAR_BACKEND_RAPIDO.bat
    echo.
) else (
    echo ✅ Processo encontrado na porta 8000
    echo.
    echo Testando conexão com o backend...
    echo.
    
    REM Tentar fazer uma requisição HTTP
    curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8000/health 2>nul
    if errorlevel 1 (
        echo ⚠️ Backend pode estar iniciando ainda...
        echo Aguarde alguns segundos e tente novamente
    ) else (
        echo ✅ Backend está respondendo!
        echo.
        echo Testando endpoint /health...
        curl -s http://localhost:8000/health
        echo.
    )
)

echo.
echo ============================================================
echo.
pause
