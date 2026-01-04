@echo off
chcp 65001 >nul
echo ============================================================
echo 🗑️ REMOVENDO PASSLIB DEFINITIVAMENTE
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo Removendo passlib...
    pip uninstall -y passlib
    echo.
    echo Verificando se passlib foi removido...
    python -c "try:
    import passlib
    print('❌ passlib AINDA está instalado!')
except ImportError:
    print('✅ passlib foi removido com sucesso!')"
    echo.
    echo Instalando apenas bcrypt...
    pip install bcrypt==4.0.1
    echo.
    echo ✅ Concluído!
    echo.
    echo Agora:
    echo 1. Pare o backend (Ctrl+C se estiver rodando)
    echo 2. Execute: INICIAR_BACKEND_FACIL.bat
    echo 3. Tente fazer login novamente
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


