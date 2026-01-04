@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 CORREÇÃO DEFINITIVA DO BANCO DE DADOS
echo ============================================================
echo.
echo Este script vai:
echo 1. Verificar onde está o banco de dados
echo 2. Verificar as colunas existentes
echo 3. Deletar e recriar as tabelas corretamente
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
    timeout /t 3 /nobreak >nul
    echo.
    
    echo Executando correção definitiva...
    echo.
    python scripts\verificar_e_corrigir_banco.py
    echo.
    echo ✅ Processo concluído!
    echo.
    echo Verifique os logs acima para confirmar que data_nascimento foi criada.
    echo.
    echo Agora execute: INICIAR_BACKEND_FACIL.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


