@echo off
echo ============================================================
echo INSTALAR DEPENDENCIAS DO PROJETO
echo ============================================================
echo.

cd /d "%~dp0"
cd backend

echo Verificando versao do Python...
python --version
echo.

echo Atualizando pip...
python -m pip install --upgrade pip
echo.

echo Tentando instalar com requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERRO com requirements.txt
    echo Tentando versao simplificada...
    echo ============================================================
    echo.
    pip install -r requirements-simple.txt
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo ERRO: Nao foi possivel instalar dependencias
        echo ============================================================
        echo.
        echo Possiveis solucoes:
        echo 1. Instalar Microsoft Visual C++ Build Tools
        echo 2. Usar Python 3.11 ou 3.12 (mais compativel)
        echo 3. Instalar manualmente: pip install pandas numpy openpyxl
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Verificando instalacao...
echo ============================================================
python -c "import sqlalchemy; print('SQLAlchemy: OK')" || echo "SQLAlchemy: FALHOU"
python -c "import pandas; print('Pandas: OK')" || echo "Pandas: FALHOU"
python -c "import fastapi; print('FastAPI: OK')" || echo "FastAPI: FALHOU"
python -c "import aiohttp; print('aiohttp: OK')" || echo "aiohttp: FALHOU"

echo.
echo Dependencias instaladas!
echo.
pause

