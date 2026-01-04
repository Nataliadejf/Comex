@echo off
echo ========================================
echo Comex Analyzer - Iniciando Backend
echo ========================================
echo.

cd /d "%~dp0backend"

echo Verificando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Criando ambiente virtual...
    python -m venv venv
    echo Ambiente virtual criado!
    echo.
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias (se necessario)...
echo Pulando smtplib e email (são built-in do Python)...
pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart --quiet
echo Tentando instalar dependências opcionais...
pip install pandas numpy openpyxl 2>&1 | findstr /V "ERROR"

echo.
echo ========================================
echo Iniciando servidor FastAPI...
echo ========================================
echo.
echo Backend estara disponivel em: http://localhost:8000
echo Documentacao da API: http://localhost:8000/docs
echo.
echo Pressione CTRL+C para parar o servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause



