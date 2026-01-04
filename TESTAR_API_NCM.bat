@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo TESTANDO BUSCA DE NCMs NA API EXTERNA
echo ============================================================
echo.

echo Verificando configuração da API...
cd backend

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

python -c "from config import settings; print(f'COMEX_STAT_API_URL: {settings.comex_stat_api_url}'); print(f'COMEX_STAT_API_KEY configurada: {settings.comex_stat_api_key is not None}')"

echo.
echo ============================================================
echo Testando busca de NCM 87083090...
echo ============================================================
echo.

curl -X GET "http://localhost:8000/dashboard/stats?meses=3&ncms=87083090&tipo_operacao=Importação" -H "accept: application/json" 2>nul | python -m json.tool | head -n 50

echo.
echo ============================================================
echo Testando busca de NCM 87089412...
echo ============================================================
echo.

curl -X GET "http://localhost:8000/dashboard/stats?meses=3&ncms=87089412&tipo_operacao=Importação" -H "accept: application/json" 2>nul | python -m json.tool | head -n 50

echo.
echo ============================================================
echo Testando busca de múltiplos NCMs...
echo ============================================================
echo.

curl -X GET "http://localhost:8000/dashboard/stats?meses=3&ncms=87083090,87089412&tipo_operacao=Importação" -H "accept: application/json" 2>nul | python -m json.tool | head -n 50

echo.
echo ============================================================
echo.
pause

