@echo off
chcp 65001 >nul
echo ============================================================
echo VERIFICAÇÃO E CORREÇÃO DE CONEXÃO COM BACKEND
echo ============================================================
echo.

echo [1/5] Verificando arquivo .env do frontend...
if not exist "frontend\.env" (
    echo    ⚠️ Arquivo .env não encontrado. Criando...
    echo REACT_APP_API_URL=https://comex-tsba.onrender.com > frontend\.env
    echo    ✅ Arquivo .env criado
) else (
    echo    ✅ Arquivo .env encontrado
    echo    Conteúdo atual:
    type frontend\.env
)

echo.
echo [2/5] Verificando se backend está acessível no Render...
curl -s -o nul -w "Status: %%{http_code}\n" https://comex-tsba.onrender.com/health
if %errorlevel% equ 0 (
    echo    ✅ Backend está acessível
) else (
    echo    ❌ Backend não está acessível
    echo    💡 Verifique:
    echo       - Se o serviço está rodando no Render Dashboard
    echo       - Se há erros nos logs do Render
    echo       - Se o health check está funcionando
)

echo.
echo [3/5] Verificando configuração do frontend...
findstr /C:"REACT_APP_API_URL" frontend\.env >nul
if %errorlevel% equ 0 (
    echo    ✅ Variável REACT_APP_API_URL encontrada
) else (
    echo    ⚠️ Variável não encontrada. Adicionando...
    echo REACT_APP_API_URL=https://comex-tsba.onrender.com >> frontend\.env
    echo    ✅ Variável adicionada
)

echo.
echo [4/5] Verificando se frontend está rodando...
netstat -ano | findstr ":3000" >nul
if %errorlevel% equ 0 (
    echo    ⚠️ Porta 3000 já está em uso
    echo    💡 Pare o processo antes de iniciar novamente
) else (
    echo    ✅ Porta 3000 está livre
)

echo.
echo [5/5] Resumo da configuração:
echo    Backend URL: https://comex-tsba.onrender.com
echo    Frontend URL: http://localhost:3000
echo.
echo ============================================================
echo PRÓXIMOS PASSOS:
echo ============================================================
echo 1. Se o backend não está acessível:
echo    - Acesse: https://dashboard.render.com
echo    - Verifique se o serviço "comex-backend" está rodando
echo    - Verifique os logs para erros
echo.
echo 2. Para iniciar o frontend localmente:
echo    cd frontend
echo    npm start
echo.
echo 3. Ou execute: INICIAR_FRONTEND.bat
echo.
echo 4. Se ainda não funcionar, tente usar backend local:
echo    - Execute: INICIAR_BACKEND.bat
echo    - Altere frontend\.env para: REACT_APP_API_URL=http://localhost:8000
echo.
pause


