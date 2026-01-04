@echo off
echo ========================================
echo Comex Analyzer - Iniciando Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

echo Verificando node_modules...
if not exist "node_modules" (
    echo [INFO] Instalando dependencias...
    call npm install
    echo.
)

echo ========================================
echo Iniciando aplicacao React...
echo ========================================
echo.
echo Frontend estara disponivel em: http://localhost:3000
echo.
echo Pressione CTRL+C para parar o servidor
echo.

npm start

pause



