@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd backend

echo.
echo ============================================================
echo VERIFICANDO DADOS DOS NCMs NO BANCO DE DADOS
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute INSTALAR_DEPENDENCIAS.bat primeiro
    pause
    exit /b 1
)

python scripts\verificar_ncms_monitorados.py

echo.
pause

