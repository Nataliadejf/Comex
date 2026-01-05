@echo off
chcp 65001 >nul
echo ========================================
echo   APROVAR CADASTROS PENDENTES
echo ========================================
echo.

cd backend
python scripts\aprovar_cadastro.py

pause

