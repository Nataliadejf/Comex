@echo off
chcp 65001 >nul
echo ============================================================
echo 👤 CRIANDO USUÁRIO DIRETAMENTE NO BANCO
echo ============================================================
echo.
echo Este script vai criar o usuário diretamente no banco,
echo contornando problemas de frontend/backend.
echo.
echo Email: nataliadejesus2@hotmail.com
echo Senha: senha123
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo Executando script...
    echo.
    python scripts\criar_usuario_direto.py
    echo.
    echo ✅ Processo concluído!
    echo.
    echo Agora você pode fazer login com:
    echo   Email: nataliadejesus2@hotmail.com
    echo   Senha: senha123
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


