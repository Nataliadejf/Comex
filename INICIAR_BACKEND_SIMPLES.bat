@echo off
chcp 65001 >nul
echo ============================================================
echo Iniciando Backend - Comex Analyzer
echo ============================================================
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
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

echo Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias essenciais...
    pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart --quiet
)

echo.
echo ============================================================
echo Iniciando servidor na porta 8000...
echo ============================================================
echo.
echo Backend estara disponivel em: http://localhost:8000
echo Documentacao: http://localhost:8000/docs
echo.
echo Pressione CTRL+C para parar o servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

