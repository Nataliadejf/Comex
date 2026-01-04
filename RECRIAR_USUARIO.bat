@echo off
chcp 65001 >nul
echo ============================================================
echo 🔄 RECRIANDO USUÁRIO COM BCRYPT DIRETO
echo ============================================================
echo.
echo Este script vai criar o usuário usando bcrypt diretamente
echo (sem passlib) para evitar problemas de compatibilidade.
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    python scripts\recriar_usuario_com_bcrypt_direto.py
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


