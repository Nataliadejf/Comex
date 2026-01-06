@echo off
echo ============================================================
echo COLETA ENRIQUECIDA DE DADOS DO MDIC
echo ============================================================
echo.
echo Este script vai coletar dados reais do portal oficial do MDIC
echo e enriquecer com empresas e CNAE.
echo.
echo IMPORTANTE:
echo - Pode levar algumas horas na primeira execucao
echo - Requer conexao com internet
echo - Os dados serao salvos no banco de dados
echo.
pause

cd /d "%~dp0"
cd backend

echo.
echo Verificando dependencias...
python -c "import sqlalchemy" 2>nul || (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

echo.
echo Iniciando coleta enriquecida...
echo.

python -c "import asyncio; import sys; from pathlib import Path; import os; os.chdir('.'); sys.path.insert(0, '.'); from data_collector.enriched_collector import EnrichedDataCollector; from database import get_db; async def coletar(): db = next(get_db()); collector = EnrichedDataCollector(); print('Iniciando coleta de 24 meses...'); stats = await collector.collect_and_enrich(db, meses=24); print('\n============================================================'); print('COLETA CONCLUIDA!'); print('============================================================'); print(f'Total de registros: {stats[\"total_registros\"]:,}'); print(f'Registros novos: {stats[\"registros_novos\"]:,}'); print(f'Registros atualizados: {stats[\"registros_atualizados\"]:,}'); print(f'Empresas enriquecidas: {stats[\"empresas_enriquecidas\"]:,}'); print(f'Meses processados: {len(stats[\"meses_processados\"])}'); if stats.get('erros'): print(f'\nErros: {len(stats[\"erros\"])}'); print('============================================================'); asyncio.run(coletar())"

if errorlevel 1 (
    echo.
    echo ERRO na coleta!
    echo Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo Coleta concluida!
echo.
pause

