@echo off
chcp 65001 >nul
echo ========================================
echo   INICIAR APLICATIVO COMEX ANALYZER
echo ========================================
echo.

REM Verificar se estamos no diretório correto
if not exist "frontend" (
    echo Erro: Diretório frontend não encontrado!
    echo Execute este script na raiz do projeto.
    pause
    exit /b 1
)

REM Verificar se .env existe
if not exist "frontend\.env" (
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=https://comex-3.onrender.com > "frontend\.env"
    echo Arquivo .env criado!
) else (
    echo Verificando configuração do .env...
    findstr /C:"REACT_APP_API_URL" "frontend\.env" >nul
    if %errorlevel% neq 0 (
        echo Adicionando REACT_APP_API_URL ao .env...
        echo REACT_APP_API_URL=https://comex-3.onrender.com >> "frontend\.env"
    ) else (
        echo .env já configurado.
    )
)

echo.
echo ========================================
echo   CONFIGURAÇÃO
echo ========================================
echo Backend: https://comex-3.onrender.com
echo Frontend: http://localhost:3000
echo.

REM Verificar se node_modules existe
if not exist "frontend\node_modules" (
    echo Instalando dependências...
    cd frontend
    call npm install
    cd ..
    echo.
)

echo ========================================
echo   INICIANDO FRONTEND
echo ========================================
echo.
echo O navegador abrirá automaticamente em alguns segundos...
echo Pressione Ctrl+C para parar o servidor.
echo.

cd frontend
call npm start

