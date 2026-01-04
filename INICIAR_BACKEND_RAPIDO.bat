@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd backend

echo.
echo ============================================================
echo INICIANDO BACKEND - COMEX ANALYZER
echo ============================================================
echo.

REM Verificar se o ambiente virtual existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ⚠️ Ambiente virtual não encontrado!
    echo Criando ambiente virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual criado e ativado
)

echo.
echo Instalando/Verificando dependências...
pip install -q fastapi uvicorn sqlalchemy python-jose[cryptography] bcrypt pydantic-settings loguru httpx certifi urllib3

echo.
echo ============================================================
echo INICIANDO SERVIDOR BACKEND
echo ============================================================
echo.
echo Backend rodando em: http://localhost:8000
echo Pressione Ctrl+C para parar
echo.
echo ============================================================
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause

