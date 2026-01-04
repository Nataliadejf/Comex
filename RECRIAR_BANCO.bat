@echo off
chcp 65001 >nul
echo ============================================================
echo ⚠️  RECRIANDO TABELA USUARIOS
echo ============================================================
echo.
echo ATENÇÃO: Isso apagará todos os usuários existentes!
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo Executando script de recriação...
    echo.
    python scripts\recriar_tabela_usuarios.py
    echo.
    echo ✅ Recriação concluída!
    echo.
    echo Agora execute: INICIAR_BACKEND_FACIL.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


