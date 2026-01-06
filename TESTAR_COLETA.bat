@echo off
echo ============================================================
echo TESTE DE COLETA ENRIQUECIDA
echo ============================================================
echo.
echo Este script vai testar a coleta passo a passo para
echo identificar problemas.
echo.
pause

cd /d "%~dp0"
cd backend

python scripts/testar_coleta_enriquecida.py

echo.
pause

