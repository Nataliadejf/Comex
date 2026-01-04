@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 TESTANDO API DIRETAMENTE
echo ============================================================
echo.

echo Testando endpoint /health...
curl http://localhost:8000/health
echo.
echo.

echo Testando endpoint /dashboard/stats sem filtros...
curl "http://localhost:8000/dashboard/stats?meses=6"
echo.
echo.

echo Testando endpoint /dashboard/stats com NCM...
curl "http://localhost:8000/dashboard/stats?meses=6&ncms=87083090"
echo.
echo.

echo ============================================================
echo ✅ TESTE CONCLUÍDO!
echo ============================================================
echo.
echo Verifique os logs do backend para mais detalhes.
echo.
pause

