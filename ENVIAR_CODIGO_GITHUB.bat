@echo off
chcp 65001 >nul
echo ============================================================
echo ENVIANDO CÓDIGO PARA GITHUB
echo ============================================================
echo.

cd /d "%~dp0"

REM Verificar se é repositório Git
if not exist ".git" (
    echo ❌ Não é um repositório Git!
    echo Execute primeiro: CRIAR_REPOSITORIO_GITHUB.bat
    pause
    exit /b 1
)

echo Cole a URL do seu repositório GitHub
echo Exemplo: https://github.com/SEU_USUARIO/comex-analyzer.git
echo.
set /p REPO_URL=

if "%REPO_URL%"=="" (
    echo ❌ URL não fornecida
    pause
    exit /b 1
)

echo.
echo Configurando remote...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo ✅ Remote configurado: %REPO_URL%
echo.

echo Adicionando todos os arquivos...
git add .
echo ✅ Arquivos adicionados
echo.

echo Fazendo commit inicial...
git commit -m "Primeiro commit - Comex Analyzer" 2>nul
if errorlevel 1 (
    echo ⚠️ Nenhuma mudança para commitar ou já existe commit
)

echo.
echo Renomeando branch para main...
git branch -M main 2>nul

echo.
echo Enviando para GitHub...
echo (Pode pedir credenciais - use seu token de acesso pessoal)
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo ⚠️ Erro ao fazer push
    echo.
    echo Possíveis soluções:
    echo 1. Verifique se a URL está correta
    echo 2. Crie um Personal Access Token:
    echo    - Acesse: https://github.com/settings/tokens
    echo    - Generate new token (classic)
    echo    - Marque: repo (todas as permissões)
    echo    - Use o token como senha quando pedir
    echo 3. Ou use GitHub Desktop: https://desktop.github.com/
    echo.
) else (
    echo.
    echo ============================================================
    echo ✅ CÓDIGO ENVIADO COM SUCESSO!
    echo ============================================================
    echo.
    echo Repositório: %REPO_URL%
    echo.
    echo Próximos passos:
    echo 1. Acesse o repositório no GitHub para verificar
    echo 2. Siga o PASSO_A_PASSO_DEPLOY.md para fazer deploy
    echo.
)

pause

