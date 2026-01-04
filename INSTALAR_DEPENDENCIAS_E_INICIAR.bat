@echo off
chcp 65001 >nul
echo ============================================================
echo 📦 INSTALANDO DEPENDÊNCIAS E INICIANDO BACKEND
echo ============================================================
echo.

cd /d "%~dp0backend"

REM Verificar se ambiente virtual existe
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Nao foi possivel criar ambiente virtual
        pause
        exit /b 1
    )
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo Instalando dependencias essenciais...
pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart certifi urllib3 requests --quiet

if errorlevel 1 (
    echo ERRO ao instalar dependencias
    pause
    exit /b 1
)

echo.
echo Verificando instalacao...
python -c "import fastapi; import uvicorn; print('✅ Dependencias instaladas corretamente')" 2>&1

if errorlevel 1 (
    echo ERRO: Dependencias nao foram instaladas corretamente
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 🚀 INICIANDO BACKEND
echo ============================================================
echo.
echo Backend estara disponivel em: http://localhost:8000
echo Documentacao: http://localhost:8000/docs
echo.
echo Pressione CTRL+C para parar o servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

