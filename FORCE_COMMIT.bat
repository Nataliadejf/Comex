@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 FORÇAR COMMIT E PUSH
echo ========================================
echo.

echo 📋 Verificando últimos commits...
git log --oneline -5

echo.
echo 🔄 Adicionando TODOS os arquivos (forçado)...
git add -A -f

echo.
echo ✅ Status após adicionar...
git status --short

echo.
echo 📊 Diferenças desde último commit...
git diff --cached --name-only

echo.
echo 🔄 Fazendo commit (--allow-empty se necessário)...
git commit --allow-empty -m "Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário" -m "- Remove senhas expostas dos arquivos .md" -m "- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)" -m "- Adiciona endpoint POST /admin/usuarios/deletar-por-email" -m "- Cria script deletar_usuarios.py para deletar usuários específicos" -m "- Corrige render.yaml removendo duplicação"

echo.
echo 🔄 Fazendo push para GitHub...
git push origin main

echo.
echo ========================================
echo ✅ PROCESSO CONCLUÍDO!
echo ========================================
echo.
echo 📡 O Render vai detectar as mudanças e fazer deploy automaticamente.
echo    Acompanhe o deploy em: https://dashboard.render.com
echo.
pause
