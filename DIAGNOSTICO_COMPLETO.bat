@echo off
chcp 65001 >nul
echo ============================================================
echo 🔍 DIAGNÓSTICO COMPLETO - API E BANCO DE DADOS
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 1️⃣  VERIFICANDO BANCO DE DADOS
echo ============================================================
echo.

python -c "from database import get_db; from sqlalchemy import text; db = next(get_db()); print('✅ Conexão com banco OK'); result = db.execute(text('SELECT COUNT(*) FROM operacoes_comex')); total = result.scalar(); print(f'Total de registros: {total}'); result2 = db.execute(text('SELECT COUNT(*) FROM operacoes_comex WHERE nome_empresa IS NOT NULL AND nome_empresa != \"\"')); com_empresa = result2.scalar(); print(f'Registros com nome_empresa: {com_empresa}'); result3 = db.execute(text('SELECT MIN(data_operacao), MAX(data_operacao) FROM operacoes_comex')); datas = result3.fetchone(); print(f'Período dos dados: {datas[0]} até {datas[1]}'); db.close()"

echo.
echo ============================================================
echo 2️⃣  TESTANDO ENDPOINT /dashboard/stats
echo ============================================================
echo.

python -c "import requests^
import json^
try:^
    r = requests.get('http://localhost:8000/dashboard/stats?meses=6')^
    print('✅ Endpoint acessível')^
    print(f'Status: {r.status_code}')^
    data = r.json()^
    print(f'Valor total USD: {data.get(\"valor_total_usd\", 0)}')^
    print(f'Empresas encontradas: {len(data.get(\"principais_empresas\", []))}')^
    print(f'NCMs encontrados: {len(data.get(\"principais_ncms\", []))}')^
except Exception as e:^
    print(f'❌ Erro: {e}')"

echo.
echo ============================================================
echo 3️⃣  VERIFICANDO COLUNA nome_empresa
echo ============================================================
echo.

python -c "from database import get_db^
from sqlalchemy import text^
db = next(get_db())^
try:^
    db.execute(text('SELECT nome_empresa FROM operacoes_comex LIMIT 1'))^
    print('✅ Coluna nome_empresa existe')^
except Exception as e:^
    print(f'❌ Coluna nome_empresa não existe: {e}')^
db.close()"

echo.
echo ============================================================
echo 4️⃣  TESTANDO QUERY DE EMPRESAS DIRETAMENTE
echo ============================================================
echo.

python -c "from database import get_db^
from database.models import OperacaoComex^
from sqlalchemy import func, and_^
from datetime import datetime, timedelta^
db = next(get_db())^
data_inicio = datetime.now() - timedelta(days=30 * 6)^
query = db.query(OperacaoComex.nome_empresa, func.sum(OperacaoComex.valor_fob).label('total_valor'), func.count(OperacaoComex.id).label('total_operacoes')).filter(and_(OperacaoComex.data_operacao >= data_inicio.date(), OperacaoComex.nome_empresa.isnot(None), OperacaoComex.nome_empresa != '')).group_by(OperacaoComex.nome_empresa).order_by(func.sum(OperacaoComex.valor_fob).desc()).limit(5).all()^
print(f'✅ Query executada com sucesso')^
print(f'Empresas encontradas: {len(query)}')^
for emp in query[:5]:^
    print(f'  - {emp[0]}: ${emp[1]:,.2f} ({emp[2]} ops)')^
db.close()"

echo.
echo ============================================================
echo ✅ DIAGNÓSTICO CONCLUÍDO!
echo ============================================================
echo.
pause
