@echo off
chcp 65001 >nul
echo ========================================
echo   CONFIGURAR FRONTEND PARA COMEX-2
echo ========================================
echo.

set "FRONTEND_ENV=frontend\.env"
set "API_URL=https://comex-2.onrender.com"

echo Configurando frontend para usar: %API_URL%
echo.

REM Verificar se o arquivo .env existe
if not exist "%FRONTEND_ENV%" (
    echo Criando arquivo .env...
    echo REACT_APP_API_URL=%API_URL% > "%FRONTEND_ENV%"
    echo Arquivo criado com sucesso!
) else (
    echo Arquivo .env encontrado. Atualizando...
    
    REM Verificar se REACT_APP_API_URL já existe
    findstr /C:"REACT_APP_API_URL" "%FRONTEND_ENV%" >nul
    if %errorlevel% equ 0 (
        REM Substituir a linha existente
        powershell -Command "(Get-Content '%FRONTEND_ENV%') -replace 'REACT_APP_API_URL=.*', 'REACT_APP_API_URL=%API_URL%' | Set-Content '%FRONTEND_ENV%'"
        echo URL atualizada!
    ) else (
        REM Adicionar nova linha
        echo REACT_APP_API_URL=%API_URL% >> "%FRONTEND_ENV%"
        echo URL adicionada!
    )
)

echo.
echo ========================================
echo   CONFIGURAÇÃO CONCLUÍDA
echo ========================================
echo.
echo Frontend configurado para usar: %API_URL%
echo.
echo IMPORTANTE: Reinicie o frontend para aplicar as mudanças!
echo Execute: REINICIAR_FRONTEND.bat
echo.
pause

