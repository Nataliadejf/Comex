@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 CORRIGINDO BCRYPT
echo ============================================================
echo.
echo Este script vai reinstalar bcrypt e passlib
echo com versões compatíveis.
echo.
pause

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo Desinstalando versões antigas...
    pip uninstall -y bcrypt passlib
    echo.
    echo Instalando bcrypt 4.0.1...
    pip install bcrypt==4.0.1
    echo.
    echo Instalando passlib[bcrypt]...
    pip install "passlib[bcrypt]==1.7.4"
    echo.
    echo ✅ Correção concluída!
    echo.
    echo Agora execute: CRIAR_USUARIO.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


