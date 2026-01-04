@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd backend

echo.
echo ============================================================
echo CONFIGURANDO API DO COMEX STAT NO ARQUIVO .env
echo ============================================================
echo.

if exist ".env" (
    echo Arquivo .env encontrado.
    echo Verificando se a configuracao da API ja existe...
    
    findstr /C:"COMEX_STAT_API_URL" .env >nul 2>&1
    if errorlevel 1 (
        echo Adicionando configuracao da API...
        echo. >> .env
        echo # API Comex Stat (MDIC) >> .env
        echo COMEX_STAT_API_URL=https://comexstat.mdic.gov.br >> .env
        echo COMEX_STAT_API_KEY= >> .env
        echo.
        echo ✅ Configuracao da API adicionada ao arquivo .env!
    ) else (
        echo ✅ Configuracao da API ja existe no arquivo .env
    )
) else (
    echo Criando arquivo .env com configuracao da API...
    (
        echo # API Comex Stat (MDIC)
        echo COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
        echo COMEX_STAT_API_KEY=
    ) > .env
    echo ✅ Arquivo .env criado com configuracao da API!
)

echo.
echo ============================================================
echo CONFIGURACAO DA API:
echo ============================================================
type .env | findstr /C:"COMEX"
echo.
echo ============================================================
echo.
echo ✅ Configuracao concluida!
echo.
echo IMPORTANTE:
echo - A URL configurada e: https://comexstat.mdic.gov.br
echo - Se voce tiver uma API key, adicione em COMEX_STAT_API_KEY
echo - Reinicie o backend para aplicar as mudancas
echo.
pause

