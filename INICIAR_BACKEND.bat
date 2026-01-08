@echo off
echo ========================================
echo   INICIANDO BACKEND
echo ========================================
echo.

cd backend

REM Verificar ambiente virtual
if exist venv\Scripts\activate.bat (
    echo Ambiente virtual encontrado!
) else (
    echo Criando ambiente virtual...
    python -m venv venv
    echo Ambiente virtual criado!
    echo.
    echo Instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo Dependencias instaladas!
)

echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo Verificando arquivo .env...
if exist .env (
    echo Arquivo .env encontrado!
) else (
    echo Criando arquivo .env basico...
    (
        echo DATABASE_URL=sqlite:///./comex.db
        echo COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
        echo SECRET_KEY=your-secret-key-here
        echo ENVIRONMENT=development
        echo DEBUG=true
    ) > .env
)

echo.
echo ========================================
echo   BACKEND INICIANDO...
echo ========================================
echo.
echo Servidor rodando em: http://localhost:8000
echo Documentacao API: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Pressione Ctrl+C para parar o servidor
echo.
echo ========================================
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000





