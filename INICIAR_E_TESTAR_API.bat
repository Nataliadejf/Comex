@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 INICIAR BACKEND E TESTAR API
echo ============================================================
echo.

REM Verificar se backend já está rodando
netstat -an | findstr ":8000" >nul
if not errorlevel 1 (
    echo ✅ Backend já está rodando na porta 8000
    echo.
    goto :testar_api
)

echo ⚠️  Backend não está rodando. Iniciando...
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo ❌ Ambiente virtual não encontrado!
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

REM Verificar dependências essenciais
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependências essenciais...
    pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt sqlalchemy pydantic pydantic-settings loguru python-dotenv python-multipart --quiet
)

echo.
echo Iniciando backend em nova janela...
echo Aguarde alguns segundos para o servidor iniciar...
echo.

start "Backend - Comex Analyzer" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Aguardar backend iniciar
echo Aguardando backend iniciar...
timeout /t 8 /nobreak >nul

:testar_api
echo.
echo ============================================================
echo 🧪 TESTANDO API
echo ============================================================
echo.

REM Verificar se backend está respondendo
python -c "import requests; import time; max_tries = 10; for i in range(max_tries): try: r = requests.get('http://localhost:8000/health', timeout=2); print(f'✅ Backend está respondendo! (Status: {r.status_code})'); break; except: if i < max_tries - 1: time.sleep(1); else: print('❌ Backend não está respondendo após 10 tentativas'); exit(1)" 2>nul

if errorlevel 1 (
    echo.
    echo ⚠️  Instalando biblioteca requests para testes...
    cd /d "%~dp0backend"
    call venv\Scripts\activate.bat
    pip install requests --quiet
    python -c "import requests; import time; max_tries = 10; for i in range(max_tries): try: r = requests.get('http://localhost:8000/health', timeout=2); print(f'✅ Backend está respondendo! (Status: {r.status_code})'); break; except: if i < max_tries - 1: time.sleep(1); else: print('❌ Backend não está respondendo'); exit(1)"
)

echo.
echo ============================================================
echo 📊 TESTANDO ENDPOINT /dashboard/stats
echo ============================================================
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat

python -c "import requests; import json; try: r = requests.get('http://localhost:8000/dashboard/stats?meses=6', timeout=10); print(f'Status: {r.status_code}'); if r.status_code == 200: data = r.json(); print(f'✅ API funcionando!'); print(f'Valor total USD: ${data.get(\"valor_total_usd\", 0):,.2f}'); print(f'Empresas: {len(data.get(\"principais_empresas\", []))}'); print(f'NCMs: {len(data.get(\"principais_ncms\", []))}'); print(f'Países: {len(data.get(\"principais_paises\", []))}'); else: print(f'❌ Erro HTTP: {r.status_code}'); except Exception as e: print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo ✅ TESTE CONCLUÍDO!
echo ============================================================
echo.
echo Backend: http://localhost:8000
echo Documentação: http://localhost:8000/docs
echo.
echo Pressione qualquer tecla para fechar...
pause >nul

