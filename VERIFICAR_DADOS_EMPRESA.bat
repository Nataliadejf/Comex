@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 VERIFICANDO DADOS DE EMPRESAS NO BANCO
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo Executando verificação...
python -c "from database import get_db; from sqlalchemy import text; db = next(get_db()); result = db.execute(text('SELECT COUNT(*) as total FROM operacoes_comex WHERE nome_empresa IS NOT NULL AND nome_empresa != \"\"')); total = result.scalar(); print(f'Total de registros com nome_empresa: {total}'); result2 = db.execute(text('SELECT nome_empresa, COUNT(*) as qtd FROM operacoes_comex WHERE nome_empresa IS NOT NULL AND nome_empresa != \"\" GROUP BY nome_empresa LIMIT 10')); empresas = result2.fetchall(); print(f'\nPrimeiras 10 empresas:'); [print(f'  - {emp[0]}: {emp[1]} operações') for emp in empresas]; db.close()"

echo.
pause

