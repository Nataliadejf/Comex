@echo off
echo ========================================
echo Criando Tabelas de Usuarios
echo ========================================
echo.

cd /d "%~dp0\backend"

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "scripts\criar_tabelas_usuarios.py"
) else (
    python "scripts\criar_tabelas_usuarios.py"
)

echo.
pause



