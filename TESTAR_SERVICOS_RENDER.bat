@echo off
chcp 65001 >nul
echo ========================================
echo   TESTAR SERVIÇOS NO RENDER
echo ========================================
echo.

echo Testando Comex-3...
echo.
curl -s https://comex-3.onrender.com/health
echo.
echo.

echo Testando Comex-2...
echo.
curl -s https://comex-2.onrender.com/health
echo.
echo.

echo ========================================
echo   TESTE CONCLUÍDO
echo ========================================
echo.
echo Se ambos retornarem JSON válido, ambos estão funcionando.
echo Use a URL do serviço que retornar {"status":"healthy"} ou similar.
echo.
pause

