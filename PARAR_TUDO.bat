@echo off
chcp 65001 >nul
echo ============================================================
echo 🛑 PARANDO TODOS OS PROCESSOS
echo ============================================================
echo.

echo Parando processos na porta 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo    Encerrando processo %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo Parando processos na porta 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo    Encerrando processo %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo Parando processos Node.js...
taskkill /F /IM node.exe >nul 2>&1

echo Parando processos Python relacionados...
for /f "tokens=2" %%a in ('tasklist ^| findstr python') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo ✅ PROCESSOS PARADOS!
echo ============================================================
echo.
pause

