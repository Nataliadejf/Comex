@echo off
echo ========================================
echo   REINICIANDO BACKEND E FRONTEND
echo ========================================
echo.

REM Parar todos os processos relacionados
echo [1/5] Parando processos existentes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul
echo Processos parados!
echo.

REM Verificar se o ambiente virtual existe
echo [2/5] Verificando ambiente virtual do backend...
cd backend
if exist venv\Scripts\activate.bat (
    echo Ambiente virtual encontrado!
) else (
    echo AVISO: Ambiente virtual nao encontrado!
    echo Criando ambiente virtual...
    python -m venv venv
    echo Ambiente virtual criado!
)
cd ..
echo.

REM Verificar arquivo .env do backend
echo [3/5] Verificando configuracoes do backend...
cd backend
if exist .env (
    echo Arquivo .env encontrado!
) else (
    echo AVISO: Arquivo .env nao encontrado!
    echo Criando arquivo .env basico...
    (
        echo DATABASE_URL=sqlite:///./comex.db
        echo COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
        echo SECRET_KEY=your-secret-key-here
        echo ENVIRONMENT=development
        echo DEBUG=true
    ) > .env
    echo Arquivo .env criado!
)
cd ..
echo.

REM Verificar arquivo .env do frontend
echo [4/5] Verificando configuracoes do frontend...
cd frontend
if exist .env (
    echo Arquivo .env encontrado!
    echo Conteudo do .env:
    type .env
) else (
    echo AVISO: Arquivo .env nao encontrado!
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=http://localhost:8000 > .env
    echo Arquivo .env criado!
)
cd ..
echo.

REM Iniciar backend em nova janela
echo [5/5] Iniciando backend e frontend...
echo.
echo ========================================
echo   BACKEND sera iniciado em nova janela
echo   FRONTEND sera iniciado nesta janela
echo ========================================
echo.
echo Aguarde alguns segundos...
echo.

REM Iniciar backend em nova janela
cd backend
start "Comex Backend" cmd /k "venv\Scripts\activate.bat && echo Backend iniciando... && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Aguardar backend iniciar
timeout /t 5 /nobreak >nul

REM Iniciar frontend nesta janela
cd frontend
echo.
echo ========================================
echo   FRONTEND INICIANDO...
echo ========================================
echo.
echo Aguarde alguns segundos para o servidor iniciar...
echo Depois acesse: http://localhost:3000
echo.
echo Backend rodando em: http://localhost:8000
echo.
echo Pressione Ctrl+C para parar o frontend
echo (O backend continuara rodando na outra janela)
echo.
echo ========================================
echo.

npm startata





