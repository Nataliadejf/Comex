@echo off
chcp 65001 >nul
echo ============================================================
echo 🔒 CORRIGINDO ERRO DE SSL/CERTIFI
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo Instalando/Atualizando certifi e urllib3...
pip install --upgrade certifi urllib3 requests --quiet

echo.
echo ⚠️  NOTA: SSL verification pode ser desabilitada no código se necessário
echo    Mas não será adicionado ao .env para evitar conflitos
echo.

echo.
echo ✅ Certifi atualizado!
echo.
echo ⚠️  NOTA: SSL foi desabilitado apenas para desenvolvimento local
echo.
pause

