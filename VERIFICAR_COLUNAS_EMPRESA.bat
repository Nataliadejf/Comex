@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 VERIFICANDO COLUNAS RELACIONADAS A EMPRESA
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

echo Verificando quais colunas existem na tabela operacoes_comex...
python -c "from database import get_db; from sqlalchemy import text, inspect; db = next(get_db()); inspector = inspect(db.bind); columns = [col['name'] for col in inspector.get_columns('operacoes_comex')]; print('Colunas na tabela operacoes_comex:'); [print(f'  - {col}') for col in sorted(columns)]; print('\nProcurando colunas relacionadas a empresa:'); empresa_cols = [col for col in columns if 'empresa' in col.lower() or 'importador' in col.lower() or 'exportador' in col.lower() or 'razao' in col.lower() or 'social' in col.lower()]; [print(f'  ✓ {col}') for col in empresa_cols] if empresa_cols else print('  ❌ Nenhuma coluna de empresa encontrada'); db.close()"

echo.
pause

