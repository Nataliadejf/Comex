@echo off
chcp 65001 >nul
echo ============================================================
echo ALIMENTAR DASHBOARD COM DADOS DAS PLANILHAS
echo ============================================================
echo.
echo Este script irá:
echo 1. Processar arquivo Excel e gerar JSONs para o dashboard
echo 2. Gerar empresas recomendadas
echo 3. Preparar dados para exibição
echo.
pause

echo.
echo [1/3] Processando arquivo Excel para dashboard...
cd backend\scripts
python carregar_dados_excel_dashboard.py
if %errorlevel% neq 0 (
    echo ❌ Erro ao processar Excel
    pause
    exit /b 1
)

echo.
echo [2/3] Gerando empresas recomendadas...
python gerar_empresas_recomendadas.py
if %errorlevel% neq 0 (
    echo ❌ Erro ao gerar empresas recomendadas
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando arquivos gerados...
cd ..\..
if exist "backend\data\resumo_dados_comexstat.json" (
    echo ✅ Resumo de dados criado
) else (
    echo ❌ Resumo de dados não encontrado
)

if exist "backend\data\empresas_recomendadas.xlsx" (
    echo ✅ Empresas recomendadas criadas
) else (
    echo ❌ Empresas recomendadas não encontradas
)

echo.
echo ============================================================
echo PRÓXIMOS PASSOS:
echo ============================================================
echo 1. Reinicie o backend (se estiver rodando)
echo 2. Acesse o dashboard no frontend
echo 3. Os dados devem aparecer automaticamente
echo.
echo Se os dados não aparecerem:
echo - Verifique se os arquivos JSON foram criados em backend\data\
echo - Verifique os logs do backend
echo - Tente recarregar a página do dashboard
echo.
pause


