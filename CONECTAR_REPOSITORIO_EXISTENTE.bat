@echo off
chcp 65001 >nul
echo ============================================================
echo CONECTAR A REPOSITÓRIO GITHUB EXISTENTE
echo ============================================================
echo.

cd /d "%~dp0"

REM Verificar se Git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git não está instalado!
    echo Baixe em: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Inicializar se não for repositório
if not exist ".git" (
    echo Inicializando repositório Git...
    git init
    echo ✅ Repositório inicializado
    echo.
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
echo Adicionando remote...
git remote add origin %REPO_URL% 2>nul
if errorlevel 1 (
    echo Tentando atualizar remote existente...
    git remote set-url origin %REPO_URL%
)

echo ✅ Remote configurado
echo.

echo Adicionando arquivos...
git add .
echo ✅ Arquivos adicionados
echo.

echo Fazendo commit...
git commit -m "Primeiro commit - Comex Analyzer" 2>nul
if errorlevel 1 (
    echo ⚠️ Nenhuma mudança para commitar ou já existe commit
)

echo.
echo Renomeando branch para main...
git branch -M main 2>nul

echo.
echo Enviando para GitHub...
echo (Pode pedir credenciais na primeira vez)
git push -u origin main

if errorlevel 1 (
    echo.
    echo ⚠️ Erro ao fazer push
    echo.
    echo Possíveis soluções:
    echo 1. Verifique se a URL está correta
    echo 2. Verifique suas credenciais GitHub
    echo 3. Tente usar GitHub Desktop: https://desktop.github.com/
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
    echo 1. Acesse o repositório no GitHub
    echo 2. Siga o PASSO_A_PASSO_DEPLOY.md para fazer deploy
    echo.
)

pause

