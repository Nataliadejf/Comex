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
echo Iniciando coleta enriquecida...
echo.

python -c "import asyncio; from data_collector.enriched_collector import EnrichedDataCollector; from database import get_db; async def coletar(): db = next(get_db()); collector = EnrichedDataCollector(); stats = await collector.collect_and_enrich(db, meses=24); print('\n============================================================'); print('COLETA CONCLUIDA!'); print('============================================================'); print(f'Total de registros: {stats[\"total_registros\"]}'); print(f'Registros novos: {stats[\"registros_novos\"]}'); print(f'Registros atualizados: {stats[\"registros_atualizados\"]}'); print(f'Empresas enriquecidas: {stats[\"empresas_enriquecidas\"]}'); print(f'Meses processados: {len(stats[\"meses_processados\"])}'); print('============================================================'); asyncio.run(coletar())"

echo.
echo Coleta concluida!
echo.
pause

