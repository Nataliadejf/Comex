@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 COMMIT E PUSH DAS MUDANÇAS
echo ========================================
echo.

echo 🔄 Adicionando arquivos modificados...
git add backend/main.py
git add frontend/src/pages/Dashboard.js
git add render.yaml
git add backend/render.yaml
git add backend/scripts/deletar_usuarios.py
git add URL_CORRETA_DATABASE.md
git add CORRIGIR_URL_POSTGRESQL.md
git add RESUMO_IMPORTACAO_ATUAL.md
git add GUIA_TESTE_PASSO_A_PASSO.md
git add commit_and_push.py
git add COMMIT_E_PUSH.bat
git add COMMIT_MUDANCAS.bat

echo.
echo ✅ Verificando status...
git status --short

echo.
echo 🔄 Fazendo commit...
git commit -m "Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário" -m "- Remove senhas expostas dos arquivos .md" -m "- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)" -m "- Adiciona endpoint POST /admin/usuarios/deletar-por-email" -m "- Cria script deletar_usuarios.py para deletar usuários específicos" -m "- Corrige render.yaml removendo duplicação"

if %errorlevel% neq 0 (
    echo ⚠️ Commit falhou - pode ser que não há mudanças ou já foram commitadas
    echo Verificando se precisa fazer push...
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
pause
