@echo off
chcp 65001 >nul
echo ============================================================
echo 📊 VERIFICANDO DADOS PARA GRÁFICOS
echo ============================================================
echo.

REM Verificar se backend está rodando
netstat -an | findstr ":8000" >nul
if errorlevel 1 (
    echo ❌ Backend NÃO está rodando na porta 8000!
    echo.
    echo Execute INICIAR_BACKEND_SIMPLES.bat primeiro
    echo Ou inicie manualmente o backend
    echo.
    pause
    exit /b 1
)

echo ✅ Backend está rodando na porta 8000
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo Testando endpoint /dashboard/stats...
python -c "import requests; import json; import urllib3; urllib3.disable_warnings(); try: r = requests.get('http://localhost:8000/dashboard/stats?meses=6', verify=False, timeout=10); print('Status:', r.status_code); if r.status_code == 200: data = r.json(); print('Valor total USD:', data.get('valor_total_usd', 0)); print('Empresas:', len(data.get('principais_empresas', []))); print('NCMs:', len(data.get('principais_ncms', []))); print('Valores por mês:', len(data.get('valores_por_mes_com_peso', []))); print('\nPrimeiros valores por mês:'); [print(f'  {item}') for item in data.get('valores_por_mes_com_peso', [])[:5]]; else: print('Erro HTTP:', r.status_code); except requests.exceptions.ConnectionError: print('❌ Erro: Backend não está respondendo'); except Exception as e: print('❌ Erro:', e)"

echo.
pause

