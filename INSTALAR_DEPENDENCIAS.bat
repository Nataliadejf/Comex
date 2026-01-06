@echo off
echo ============================================================
echo INSTALAR DEPENDENCIAS DO PROJETO
echo ============================================================
echo.

cd /d "%~dp0"
cd backend

echo Instalando dependencias do backend...
pip install -r requirements.txt

echo.
echo Dependencias instaladas!
echo.
pause

