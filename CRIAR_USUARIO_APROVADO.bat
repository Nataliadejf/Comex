@echo off
chcp 65001 >nul
echo ========================================
echo   CRIAR USUÁRIO APROVADO
echo ========================================
echo.

cd backend
python scripts\criar_usuario_aprovado.py

pause

