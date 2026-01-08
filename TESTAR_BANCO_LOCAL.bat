@echo off
echo ========================================
echo TESTE DO BANCO DE DADOS - LOCAL
echo ========================================
echo.

cd /d "%~dp0"
cd backend

echo Verificando se o ambiente virtual existe...
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else (
    echo Ambiente virtual nao encontrado. Criando...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo.
echo Instalando dependencias...
pip install -q -r requirements.txt

echo.
echo Executando teste do banco de dados...
echo.

python scripts/testar_banco.py

echo.
echo ========================================
echo Teste concluido!
echo ========================================
pause



