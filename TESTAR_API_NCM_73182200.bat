@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd backend

echo.
echo ============================================================
echo TESTANDO API COM NCM 73182200
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

python scripts\testar_api_ncm_direto.py

echo.
pause

