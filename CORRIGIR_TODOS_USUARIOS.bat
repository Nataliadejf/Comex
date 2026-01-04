@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 CORRIGINDO TODOS OS USUÁRIOS
echo ============================================================
echo.
echo Este script vai recriar os hashes de TODOS os usuários
echo usando bcrypt direto (sem passlib).
echo.
echo ⚠️ ATENÇÃO: Todos os usuários terão a senha resetada para:
echo    senha123
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    python scripts\corrigir_todos_usuarios.py
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


