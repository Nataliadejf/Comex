@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 COMMIT E PUSH DAS MUDANÇAS
echo ========================================
echo.

echo 🔄 Adicionando arquivos ao stage...
git add -A
if %errorlevel% neq 0 (
    echo ❌ Erro ao adicionar arquivos
    pause
    exit /b 1
)

echo.
echo ✅ Verificando status...
git status --short

echo.
echo 🔄 Fazendo commit...
git commit -m "Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário

- Remove senhas expostas dos arquivos .md
- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)
- Adiciona endpoint POST /admin/usuarios/deletar-por-email
- Cria script deletar_usuarios.py para deletar usuários específicos
- Corrige render.yaml removendo duplicação"

if %errorlevel% neq 0 (
    echo ❌ Erro ao fazer commit
    pause
    exit /b 1
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
