@echo off
echo ============================================================
echo TESTE DE COLETA ENRIQUECIDA
echo ============================================================
echo.
echo Este script vai testar a coleta passo a passo para
echo identificar problemas.
echo.
echo Verificando dependencias...
echo.

cd /d "%~dp0"
cd backend

echo Verificando se Python esta instalado...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    pause
    exit /b 1
)

echo.
echo Verificando se dependencias estao instaladas...
python -c "import sqlalchemy; print('SQLAlchemy: OK')" 2>nul || (
    echo SQLAlchemy nao encontrado. Instalando dependencias...
    pip install -r requirements.txt
)

python -c "import pandas; print('Pandas: OK')" 2>nul || (
    echo Pandas nao encontrado. Instalando...
    pip install pandas openpyxl
)

echo.
echo Iniciando teste...
echo.

python scripts/testar_coleta_enriquecida.py

echo.
pause

