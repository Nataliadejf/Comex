@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo TESTANDO BUSCA DE NCMs NO BACKEND
echo ============================================================
echo.

echo Testando NCM 87083090 (deve ter dados)...
curl -X GET "http://localhost:8000/dashboard/stats?meses=12&ncms=87083090" -H "accept: application/json" 2>nul | python -m json.tool

echo.
echo ============================================================
echo.

echo Testando outro NCM (ex: 87089900)...
curl -X GET "http://localhost:8000/dashboard/stats?meses=12&ncms=87089900" -H "accept: application/json" 2>nul | python -m json.tool

echo.
echo ============================================================
echo.

echo Testando múltiplos NCMs...
curl -X GET "http://localhost:8000/dashboard/stats?meses=12&ncms=87083090,87089900" -H "accept: application/json" 2>nul | python -m json.tool

echo.
echo ============================================================
echo.
pause

