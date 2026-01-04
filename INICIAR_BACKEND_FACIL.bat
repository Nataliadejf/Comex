@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 INICIANDO BACKEND - COMEX ANALYZER
echo ============================================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

REM Verificar se estamos na pasta correta
if not exist "backend" (
    echo ❌ ERRO: Pasta 'backend' não encontrada!
    echo Certifique-se de executar este script da pasta raiz do projeto.
    pause
    exit /b 1
)

cd backend

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

REM Verificar se as dependências estão instaladas
echo 📦 Verificando dependências essenciais...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependências essenciais não encontradas. Instalando...
    echo Instalando dependências mínimas primeiro...
    pip install -r requirements-minimal.txt
    if errorlevel 1 (
        echo ❌ ERRO ao instalar dependências mínimas!
        echo Tentando instalar manualmente...
        pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart
        if errorlevel 1 (
            echo ❌ ERRO ao instalar dependências essenciais!
            pause
            exit /b 1
        )
    )
    echo ✅ Dependências essenciais instaladas
    echo.
    echo 📦 Tentando instalar dependências opcionais (pandas, numpy)...
    echo ⚠️  Se falhar, não é crítico - login/cadastro funcionará mesmo assim
    pip install pandas numpy openpyxl 2>&1 | findstr /V "ERROR"
    echo.
) else (
    REM Verificar especificamente python-jose
    pip show python-jose >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  python-jose não encontrado. Instalando...
        pip install python-jose[cryptography]
    )
    REM Verificar bcrypt
    pip show bcrypt >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  bcrypt não encontrado. Instalando...
        pip install bcrypt==4.0.1
    )
    echo ✅ Dependências essenciais OK
    echo.
)

REM Parar processos na porta 8000
echo 🔄 Parando processos na porta 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo    Encerrando processo %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

REM Iniciar servidor
echo ============================================================
echo 🚀 INICIANDO SERVIDOR NA PORTA 8000...
echo ============================================================
echo.
echo ⚠️  IMPORTANTE: Mantenha esta janela aberta!
echo ⚠️  Para parar o servidor, pressione CTRL+C
echo.
echo 📍 Acesse: http://localhost:8000/health
echo.
echo ============================================================
echo.

echo Testando import do main.py antes de iniciar...
python -c "from main import app; print('✅ Import OK')" 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERRO ao importar main.py!
    echo.
    echo Executando diagnóstico detalhado...
    python -c "import sys; sys.path.insert(0, '.'); from main import app" 2>&1
    echo.
    echo Execute DIAGNOSTICO_BACKEND.bat para mais detalhes
    echo.
    pause
    exit /b 1
)

echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo ❌ ERRO ao iniciar servidor!
    echo.
    echo Verifique:
    echo 1. Se todas as dependências estão instaladas
    echo 2. Se o arquivo main.py existe
    echo 3. Se há erros no código Python
    echo 4. Execute DIAGNOSTICO_BACKEND.bat para diagnóstico completo
    echo.
    pause
)

