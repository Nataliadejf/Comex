@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 TESTANDO LOGIN DIRETO
echo ============================================================
echo.
echo Este script vai testar o login diretamente no banco,
echo sem passar pelo frontend, para identificar onde está o problema.
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    python scripts\testar_login_direto.py
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


