@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd backend

echo.
echo ============================================================
echo VERIFICANDO NCM 73182200 NO BANCO DE DADOS
echo ============================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ⚠️ Ambiente virtual não encontrado!
    echo Tentando continuar mesmo assim...
    echo.
)

REM Verificar se sqlalchemy está instalado
python -c "import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependências necessárias...
    pip install sqlalchemy loguru >nul 2>&1
)

REM Executar o script Python
python scripts\verificar_ncm_banco.py

echo.
pause

