@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 DIAGNÓSTICO DO BACKEND
echo ============================================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

if not exist "backend" (
    echo ❌ ERRO: Pasta 'backend' não encontrada!
    pause
    exit /b 1
)

cd backend

echo 📁 Diretório atual: %CD%
echo.

echo 1️⃣ Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python não encontrado!
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo 2️⃣ Verificando ambiente virtual...
if exist "venv\Scripts\activate.bat" (
    echo ✅ Ambiente virtual encontrado
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual criado e ativado
)
echo.

echo 3️⃣ Verificando dependências principais...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ❌ FastAPI não encontrado!
    echo Instalando dependências...
    pip install -r requirements.txt
) else (
    echo ✅ FastAPI encontrado
)

pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo ❌ Uvicorn não encontrado!
    pip install uvicorn[standard]
) else (
    echo ✅ Uvicorn encontrado
)

pip show bcrypt >nul 2>&1
if errorlevel 1 (
    echo ❌ Bcrypt não encontrado!
    pip install bcrypt==4.0.1
) else (
    echo ✅ Bcrypt encontrado
)

pip show python-jose >nul 2>&1
if errorlevel 1 (
    echo ❌ python-jose não encontrado!
    pip install python-jose[cryptography]
) else (
    echo ✅ python-jose encontrado
)
echo.

echo 4️⃣ Verificando sintaxe do main.py...
python -m py_compile main.py
if errorlevel 1 (
    echo ❌ ERRO DE SINTAXE no main.py!
    pause
    exit /b 1
) else (
    echo ✅ Sintaxe OK
)
echo.

echo 5️⃣ Tentando importar módulos principais...
python -c "from main import app; print('✅ main.py importado com sucesso')" 2>&1
if errorlevel 1 (
    echo ❌ ERRO ao importar main.py!
    echo.
    echo Executando import detalhado...
    python -c "import sys; sys.path.insert(0, '.'); from main import app" 2>&1
    pause
    exit /b 1
)
echo.

echo 6️⃣ Verificando porta 8000...
netstat -aon | findstr :8000 | findstr LISTENING
if not errorlevel 1 (
    echo ⚠️  Porta 8000 já está em uso!
    echo.
    echo Processos usando a porta 8000:
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
        echo    PID: %%a
        tasklist /FI "PID eq %%a" /FO LIST | findstr "Nome da Imagem"
    )
    echo.
    echo Deseja encerrar esses processos? (S/N)
    set /p resposta=
    if /i "%resposta%"=="S" (
        for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        echo ✅ Processos encerrados
        timeout /t 2 /nobreak >nul
    )
) else (
    echo ✅ Porta 8000 livre
)
echo.

echo ============================================================
echo ✅ DIAGNÓSTICO CONCLUÍDO
echo ============================================================
echo.
echo Agora você pode executar: INICIAR_BACKEND_FACIL.bat
echo.
pause

