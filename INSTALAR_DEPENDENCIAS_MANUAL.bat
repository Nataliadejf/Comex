@echo off
echo ============================================================
echo INSTALAR DEPENDENCIAS MANUALMENTE (PASSO A PASSO)
echo ============================================================
echo.
echo Este script instala as dependencias uma por uma
echo para identificar qual esta causando problema.
echo.

cd /d "%~dp0"
cd backend

echo Atualizando pip...
python -m pip install --upgrade pip
echo.

echo 1. Instalando FastAPI e Uvicorn...
pip install fastapi uvicorn[standard]
echo.

echo 2. Instalando Pydantic...
pip install pydantic pydantic-settings
echo.

echo 3. Instalando SQLAlchemy...
pip install sqlalchemy
echo.

echo 4. Instalando NumPy...
pip install numpy
echo.

echo 5. Instalando Pandas...
pip install pandas
if errorlevel 1 (
    echo.
    echo ERRO ao instalar pandas!
    echo Tentando versao mais recente...
    pip install --upgrade pandas
)
echo.

echo 6. Instalando openpyxl...
pip install openpyxl
echo.

echo 7. Instalando aiohttp e httpx...
pip install aiohttp httpx
echo.

echo 8. Instalando outras dependencias...
pip install python-dotenv schedule loguru passlib[bcrypt] PyJWT psycopg2-binary python-multipart
echo.

echo ============================================================
echo Verificando instalacao...
echo ============================================================
python -c "import sqlalchemy; print('SQLAlchemy: OK')" || echo "SQLAlchemy: FALHOU"
python -c "import pandas; print('Pandas: OK')" || echo "Pandas: FALHOU"
python -c "import fastapi; print('FastAPI: OK')" || echo "FastAPI: FALHOU"
python -c "import aiohttp; print('aiohttp: OK')" || echo "aiohttp: FALHOU"

echo.
echo Instalacao concluida!
echo.
pause

