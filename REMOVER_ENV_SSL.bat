@echo off
chcp 65001 >nul
echo ============================================================
echo 🗑️  REMOVENDO CONFIGURAÇÃO SSL DO .ENV
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist ".env" (
    echo Removendo linha SSL_VERIFY do .env...
    findstr /V "SSL_VERIFY" .env > .env.tmp
    move /Y .env.tmp .env >nul
    echo ✅ Linha SSL_VERIFY removida do .env
) else (
    echo ✅ Arquivo .env não existe ou não tem SSL_VERIFY
)

echo.
pause

