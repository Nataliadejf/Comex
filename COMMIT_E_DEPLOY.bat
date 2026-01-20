@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 COMMIT E DEPLOY DAS CORREÇÕES
echo ========================================
echo.

echo 📋 Verificando status...
git status --short

echo.
echo 🔄 Adicionando TODOS os arquivos modificados...
git add -A

echo.
echo ✅ Status após adicionar...
git status --short

echo.
echo 🔄 Fazendo commit...
git commit -m "fix: Corrige erro React #310 e melhora tratamento BigQuery" -m "React:" -m "- Move useEffect para topo do componente (regra dos hooks)" -m "- Corrige erro React #310 causado por hooks fora de ordem" -m "" -m "Frontend:" -m "- Melhora script postbuild para criar _redirects" -m "- Garante que _redirects seja criado no build" -m "" -m "Backend:" -m "- Melhora tratamento de erro BigQuery (403)" -m "- Retorna lista vazia sem quebrar aplicação" -m "- Logs detalhados para debugging"

if %errorlevel% neq 0 (
    echo ⚠️ Commit falhou - pode já estar tudo commitado
    git status
    pause
)

echo.
echo 🔄 Fazendo push para GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo ❌ Erro ao fazer push
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ COMMIT E PUSH CONCLUÍDOS COM SUCESSO!
echo ========================================
echo.
echo 📡 O Render vai detectar as mudanças e fazer deploy automaticamente.
echo    Acompanhe o deploy em: https://dashboard.render.com
echo.
echo ⏱️ Tempo estimado para deploy:
echo    - Backend: 5-10 minutos
echo    - Frontend: 3-5 minutos
echo.
echo 🔍 Após o deploy, verifique:
echo    - Dashboard não deve mais mostrar erro React #310
echo    - Frontend deve carregar corretamente
echo    - BigQuery deve retornar lista vazia sem quebrar a aplicação
echo.
pause
