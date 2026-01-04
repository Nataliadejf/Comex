@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 VERIFICANDO SERVIDORES
echo ============================================================
echo.

echo 📋 Verificando portas em uso...
echo.

echo 🔵 Backend (porta 8000):
netstat -ano | findstr ":8000" | findstr "LISTENING"
if errorlevel 1 (
    echo ❌ Backend NÃO está rodando na porta 8000
    echo    Execute: INICIAR_BACKEND_FACIL.bat
) else (
    echo ✅ Backend está rodando na porta 8000
)
echo.

echo 🟢 Frontend (porta 3000):
netstat -ano | findstr ":3000" | findstr "LISTENING"
if errorlevel 1 (
    echo ❌ Frontend NÃO está rodando na porta 3000
    echo    Execute: INICIAR_FRONTEND.bat
) else (
    echo ✅ Frontend está rodando na porta 3000
)
echo.

echo 🟡 Frontend alternativo (porta 3004):
netstat -ano | findstr ":3004" | findstr "LISTENING"
if errorlevel 1 (
    echo ℹ️  Nenhum servidor na porta 3004
) else (
    echo ⚠️  Servidor encontrado na porta 3004
)
echo.

echo ============================================================
echo 📋 RESUMO
echo ============================================================
echo.
echo Para iniciar os servidores:
echo   1. Backend:  INICIAR_BACKEND_FACIL.bat
echo   2. Frontend: INICIAR_FRONTEND.bat
echo.
echo Acesse o frontend em: http://localhost:3000
echo.
pause

