@echo off
echo ========================================
echo TESTE DO BANCO DE DADOS
echo ========================================
echo.

cd /d "%~dp0"
cd backend

echo Executando teste do banco de dados...
echo.

python scripts/testar_banco.py

echo.
echo ========================================
echo Teste concluido!
echo ========================================
pause



