@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 COMMIT E PUSH FINAL
echo ========================================
echo.

echo 📋 Verificando status...
git status --short

echo.
echo 🔄 Adicionando TODOS os arquivos...
git add -A

echo.
echo ✅ Status após adicionar...
git status --short

echo.
echo 🔄 Fazendo commit...
git commit -m "Implementa melhorias mobile, UF completo e corrige BigQuery" -m "Mobile:" -m "- Sidebar colapsável com overlay em telas pequenas" -m "- Botão toggle sempre visível no header" -m "- Cards, gráficos e tabelas responsivos" -m "- Padding e fontes ajustadas para mobile" -m "" -m "UF/Estado:" -m "- Usa coluna 'UF Produto' do Excel com fallback" -m "- Exibe nome completo do estado nas tabelas" -m "- Backend retorna uf_nome_completo" -m "- Frontend converte UF para nome completo" -m "" -m "BigQuery:" -m "- Corrige acesso aos dados (atributos vs dicionário)" -m "- Adiciona DISTINCT e validação de dados" -m "- Logs detalhados para debugging" -m "- Tratamento de erros aprimorado"

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
echo 🔍 Após o deploy, verifique os logs do backend para validar:
echo    - Sugestões de empresas do BigQuery
echo    - Nomes completos dos estados nas tabelas
echo    - Responsividade mobile do dashboard
echo.
pause
