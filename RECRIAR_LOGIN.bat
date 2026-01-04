@echo off
chcp 65001 >nul
echo ============================================================
echo 🔄 DELETANDO E RECRIANDO TABELAS DE LOGIN E APROVAÇÃO
echo ============================================================
echo.
echo Este script vai:
echo 1. Deletar as tabelas usuarios e aprovacoes_cadastro
echo 2. Recriar elas do zero com todas as colunas corretas
echo.
echo ⚠️  ATENÇÃO: Todos os usuários serão apagados!
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    
    echo Parando backend se estiver rodando...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
        echo    Encerrando processo %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo.
    
    echo Executando script de recriação...
    echo.
    python scripts\deletar_e_recriar_login.py
    echo.
    echo ✅ Processo concluído!
    echo.
    echo Agora execute: INICIAR_BACKEND_FACIL.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


