@echo off
chcp 65001 >nul
echo ============================================================
echo 📦 INSTALANDO DEPENDÊNCIAS DO BACKEND
echo ============================================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0backend"

echo 📁 Diretório: %CD%
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo Instale Python de https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

REM Verificar se o ambiente virtual existe
if not exist "venv" (
    echo ⚠️  Ambiente virtual não encontrado. Criando...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ ERRO ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado
    echo.
)

REM Ativar ambiente virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
) else (
    echo ❌ ERRO: Script de ativação não encontrado!
    pause
    exit /b 1
)

REM Atualizar pip
echo 📦 Atualizando pip...
python -m pip install --upgrade pip
echo.

REM Instalar dependências
echo ============================================================
echo 📦 INSTALANDO DEPENDÊNCIAS...
echo ============================================================
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ ERRO ao instalar dependências!
    echo.
    echo Tentando instalar manualmente as principais...
    echo.
    pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] sqlalchemy pydantic pydantic-settings loguru python-dotenv
    echo.
)

echo.
echo ============================================================
echo ✅ INSTALAÇÃO CONCLUÍDA!
echo ============================================================
echo.
echo Agora você pode executar: INICIAR_BACKEND_FACIL.bat
echo.
pause


