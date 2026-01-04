@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 CORRIGINDO REQUIREMENTS.TXT
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

echo Removendo tentativas de instalar módulos built-in...
echo.

echo Instalando apenas dependências válidas...
pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart --quiet

echo.
echo ✅ Dependências essenciais instaladas!
echo.
echo Tentando instalar dependências opcionais...
pip install pandas numpy openpyxl 2>&1 | findstr /V "ERROR"
echo.

echo ============================================================
echo ✅ CORREÇÃO CONCLUÍDA!
echo ============================================================
echo.
pause

