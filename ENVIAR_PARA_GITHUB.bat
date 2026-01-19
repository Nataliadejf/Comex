@echo off
chcp 65001 >nul
echo ============================================================
echo ENVIAR MUDANÇAS PARA GITHUB E RENDER
echo ============================================================
echo.
echo Este script irá:
echo 1. Adicionar todas as mudanças ao Git
echo 2. Fazer commit com mensagem descritiva
echo 3. Enviar para o GitHub
echo 4. O Render fará deploy automático
echo.
pause

echo.
echo [1/4] Verificando status do Git...
git status --short

echo.
echo [2/4] Adicionando arquivos modificados e novos...
git add backend/main.py
git add frontend/src/pages/Dashboard.js
git add frontend/src/services/api.js
git add backend/scripts/carregar_dados_excel_dashboard.py
git add backend/scripts/gerar_empresas_recomendadas.py
git add backend/data_collector/empresa_*.py
git add ALIMENTAR_DASHBOARD.bat
git add COMO_ALIMENTAR_DASHBOARD.md
git add SOLUCAO_CONEXAO_RENDER.md
git add VERIFICAR_CONEXAO.ps1
git add CORRIGIR_URL_BACKEND.bat
git add VERIFICAR_E_CORRIGIR_CONEXAO.bat

echo.
echo Adicionando outros arquivos modificados...
git add -u

echo.
echo [3/4] Fazendo commit...
git commit -m "fix: Corrigir erros de conexão e dados vazios no dashboard

- Remover health check bloqueante no frontend
- Melhorar tratamento de erros para não bloquear quando backend não está acessível
- Garantir que endpoints retornem dados vazios elegantes quando arquivos não existem
- Corrigir tratamento de erros nas APIs de empresas recomendadas e ComexStat
- Atualizar URL do backend para https://comex-4.onrender.com
- Melhorar logs de erro no backend para facilitar debug"

if errorlevel 1 (
    echo ⚠️ Erro ao fazer commit. Verifique se há mudanças para commitar.
    pause
    exit /b 1
)

echo.
echo [4/4] Enviando para GitHub...
git push origin main

if errorlevel 0 (
    echo.
    echo ============================================================
    echo ✅ SUCESSO!
    echo ============================================================
    echo.
    echo Mudanças enviadas para GitHub com sucesso!
    echo.
    echo O Render irá fazer deploy automático em alguns minutos.
    echo.
    echo Para acompanhar o deploy:
    echo 1. Acesse: https://dashboard.render.com
    echo 2. Vá para o serviço "comex-backend"
    echo 3. Verifique a aba "Events" ou "Logs"
    echo.
    echo Após o deploy, os novos endpoints estarão disponíveis:
    echo - /dashboard/empresas-importadoras
    echo - /dashboard/empresas-exportadoras
    echo - /dashboard/empresas-recomendadas
    echo.
) else (
    echo.
    echo ❌ Erro ao enviar para GitHub
    echo Verifique sua conexão e credenciais do Git
    echo.
)

pause


