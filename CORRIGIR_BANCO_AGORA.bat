@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 CORRIGINDO BANCO DE DADOS - SOLUÇÃO DEFINITIVA
echo ============================================================
echo.
echo Este script vai recriar a tabela usuarios com todas as colunas.
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
    echo Executando correção do banco...
    echo.
    python scripts\recriar_tabela_usuarios.py
    echo.
    echo ✅ Correção concluída!
    echo.
    echo Agora execute: INICIAR_BACKEND_FACIL.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


