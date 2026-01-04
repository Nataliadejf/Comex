@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 TESTE COMPLETO DA API
echo ============================================================
echo.

echo Verificando se o backend está rodando...
netstat -an | findstr ":8000" >nul
if errorlevel 1 (
    echo ❌ Backend NÃO está rodando na porta 8000!
    echo.
    echo Execute INICIAR_BACKEND_FACIL.bat primeiro
    pause
    exit /b 1
) else (
    echo ✅ Backend está rodando na porta 8000
)

echo.
echo ============================================================
echo 1️⃣  TESTANDO ENDPOINT /health
echo ============================================================
echo.

python -c "import requests; import json; try: r = requests.get('http://localhost:8000/health', timeout=5); print(f'Status: {r.status_code}'); print(f'Resposta: {json.dumps(r.json(), indent=2, ensure_ascii=False)}'); except requests.exceptions.ConnectionError: print('❌ Erro: Não foi possível conectar ao backend'); except Exception as e: print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo 2️⃣  TESTANDO ENDPOINT /dashboard/stats (sem filtros)
echo ============================================================
echo.

python -c "import requests; import json; try: r = requests.get('http://localhost:8000/dashboard/stats?meses=6', timeout=10); print(f'Status: {r.status_code}'); if r.status_code == 200: data = r.json(); print(f'✅ API funcionando!'); print(f'Valor total USD: ${data.get(\"valor_total_usd\", 0):,.2f}'); print(f'Empresas: {len(data.get(\"principais_empresas\", []))}'); print(f'NCMs: {len(data.get(\"principais_ncms\", []))}'); print(f'Países: {len(data.get(\"principais_paises\", []))}'); else: print(f'❌ Erro HTTP: {r.status_code}'); print(r.text[:500]); except requests.exceptions.ConnectionError: print('❌ Erro: Não foi possível conectar ao backend'); except Exception as e: print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo 3️⃣  TESTANDO ENDPOINT /dashboard/stats (com NCM)
echo ============================================================
echo.

python -c "import requests; import json; try: r = requests.get('http://localhost:8000/dashboard/stats?meses=6&ncms=87083090', timeout=10); print(f'Status: {r.status_code}'); if r.status_code == 200: data = r.json(); print(f'✅ API funcionando com filtro NCM!'); print(f'Valor total USD: ${data.get(\"valor_total_usd\", 0):,.2f}'); print(f'Empresas: {len(data.get(\"principais_empresas\", []))}'); else: print(f'❌ Erro HTTP: {r.status_code}'); except requests.exceptions.ConnectionError: print('❌ Erro: Não foi possível conectar ao backend'); except Exception as e: print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo 4️⃣  TESTANDO CORS (Cross-Origin)
echo ============================================================
echo.

python -c "import requests; try: headers = {'Origin': 'http://localhost:3000'}; r = requests.options('http://localhost:8000/dashboard/stats', headers=headers, timeout=5); print(f'Status OPTIONS: {r.status_code}'); cors_headers = {k: v for k, v in r.headers.items() if 'access-control' in k.lower()}; if cors_headers: print('✅ CORS configurado:'); [print(f'  {k}: {v}') for k, v in cors_headers.items()]; else: print('⚠️  Cabeçalhos CORS não encontrados'); except Exception as e: print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo 5️⃣  VERIFICANDO CONFIGURAÇÃO DO FRONTEND
echo ============================================================
echo.

cd /d "%~dp0frontend\src\services"

if exist "api.js" (
    echo ✅ Arquivo api.js encontrado
    findstr /C:"localhost:8000" api.js >nul
    if errorlevel 1 (
        echo ⚠️  URL da API não encontrada em api.js
    ) else (
        echo ✅ URL da API configurada corretamente
        findstr /C:"localhost:8000" api.js
    )
) else (
    echo ❌ Arquivo api.js não encontrado!
)

echo.
echo ============================================================
echo ✅ TESTE CONCLUÍDO!
echo ============================================================
echo.
pause

