@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 INICIAR BACKEND E VERIFICAR DADOS
echo ============================================================
echo.

REM Verificar se backend já está rodando
netstat -an | findstr ":8000" >nul
if not errorlevel 1 (
    echo ✅ Backend já está rodando
    echo.
    goto :verificar_dados
)

echo Iniciando backend...
cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

start "Backend - Comex Analyzer" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Aguardando backend iniciar...
timeout /t 8 /nobreak >nul

:verificar_dados
echo.
echo ============================================================
echo 📊 VERIFICANDO DADOS
echo ============================================================
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat

python -c "import requests; import json; import urllib3; urllib3.disable_warnings(); import time; max_tries = 10; for i in range(max_tries): try: r = requests.get('http://localhost:8000/health', verify=False, timeout=2); print('✅ Backend respondendo!'); break; except: if i < max_tries - 1: time.sleep(1); else: print('❌ Backend não está respondendo'); exit(1)"

echo.
echo Testando endpoint /dashboard/stats...
python -c "import requests; import json; import urllib3; urllib3.disable_warnings(); try: r = requests.get('http://localhost:8000/dashboard/stats?meses=6', verify=False, timeout=10); print('Status:', r.status_code); if r.status_code == 200: data = r.json(); print('✅ API funcionando!'); print('Valor total USD:', data.get('valor_total_usd', 0)); print('Empresas:', len(data.get('principais_empresas', []))); print('NCMs:', len(data.get('principais_ncms', []))); print('Valores por mês:', len(data.get('valores_por_mes_com_peso', []))); if len(data.get('valores_por_mes_com_peso', [])) > 0: print('\nPrimeiros valores por mês:'); [print(f'  Mês: {item.get(\"mes\", \"N/A\")}, Valor: {item.get(\"valor_fob\", 0)}') for item in data.get('valores_por_mes_com_peso', [])[:5]]; else: print('⚠️  Nenhum valor por mês retornado'); else: print('Erro HTTP:', r.status_code); except requests.exceptions.ConnectionError: print('❌ Erro: Backend não está respondendo'); except Exception as e: print('❌ Erro:', e)"

echo.
echo ============================================================
echo ✅ VERIFICAÇÃO CONCLUÍDA!
echo ============================================================
echo.
pause

