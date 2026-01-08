@echo off
echo ========================================
echo   INICIANDO FRONTEND
echo ========================================
echo.

cd frontend

echo Parando processos do Node existentes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Verificando arquivo .env...
if exist .env (
    echo Arquivo .env encontrado!
    echo Conteudo:
    type .env
    echo.
) else (
    echo AVISO: Arquivo .env nao encontrado!
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=http://localhost:8000 > .env
    echo Arquivo .env criado!
)

echo.
echo Verificando dependencias...
if exist node_modules (
    echo Dependencias instaladas!
) else (
    echo Instalando dependencias...
    call npm install
    echo Dependencias instaladas!
)

echo.
echo ========================================
echo   FRONTEND INICIANDO...
echo ========================================
echo.
echo Aguarde alguns segundos para o servidor iniciar...
echo Depois acesse: http://localhost:3000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.
echo ========================================
echo.

npm start





