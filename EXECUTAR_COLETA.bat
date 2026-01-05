@echo off
echo ========================================
echo EXECUTAR COLETA DE DADOS
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python e tente novamente.
    pause
    exit /b 1
)

REM Verificar backend primeiro
echo Verificando backend antes de coletar...
echo.
python backend\scripts\diagnosticar_backend.py --url https://comex-backend-wjco.onrender.com >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  Backend pode nao estar acessivel.
    echo    Deseja continuar mesmo assim? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo Cancelado.
        pause
        exit /b 0
    )
)

echo.
echo Executando coleta de dados...
echo.
python backend\scripts\executar_coleta.py --meses 24

echo.
echo ========================================
echo COLETA CONCLUIDA
echo ========================================
echo.
echo Para avaliar o metodo usado, execute:
echo   AVALIAR_METODO.bat
echo.
pause

