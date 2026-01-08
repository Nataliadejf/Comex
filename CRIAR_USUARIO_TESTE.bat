@echo off
echo ========================================
echo Criando Usuario de Teste
echo ========================================
echo.

cd /d "%~dp0\backend"

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "scripts\criar_usuario_teste.py"
) else (
    python "scripts\criar_usuario_teste.py"
)

echo.
echo Usuario criado:
echo Email: nataliadejesus2@hotmail.com
echo Senha: senha123
echo.
pause



