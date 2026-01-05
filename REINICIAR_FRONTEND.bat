@echo off
echo ========================================
echo   REINICIANDO FRONTEND
echo ========================================
echo.

cd frontend

echo Parando processos do Node...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Verificando arquivo .env...
if exist .env (
    echo Conteudo do .env:
    type .env
    echo.
) else (
    echo AVISO: Arquivo .env nao encontrado!
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=https://comex-tsba.onrender.com > .env
)

echo.
echo Iniciando frontend...
echo.
echo Aguarde alguns segundos para o servidor iniciar...
echo Depois acesse: http://localhost:3000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

npm start

