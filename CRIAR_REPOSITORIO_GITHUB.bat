@echo off
chcp 65001 >nul
echo ============================================================
echo CRIANDO REPOSITÓRIO NO GITHUB
echo ============================================================
echo.

cd /d "%~dp0"

REM Verificar se Git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git não está instalado!
    echo.
    echo Baixe em: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git encontrado
echo.

REM Verificar se já é um repositório Git
if exist ".git" (
    echo ⚠️ Já é um repositório Git
    echo.
    git remote -v 2>nul
    if errorlevel 1 (
        echo Repositório local sem remote configurado.
    ) else (
        echo.
        echo Já existe um remote configurado.
        echo Deseja criar um novo repositório? (S/N)
        set /p RESPOSTA=
        if /i not "%RESPOSTA%"=="S" (
            echo Cancelado.
            pause
            exit /b 0
        )
    )
) else (
    echo Inicializando repositório Git...
    git init
    echo ✅ Repositório inicializado
    echo.
)

REM Verificar se GitHub CLI está instalado
where gh >nul 2>&1
if errorlevel 1 (
    echo ⚠️ GitHub CLI não encontrado
    echo.
    echo OPÇÃO 1: Instalar GitHub CLI (recomendado)
    echo   1. Baixe: https://cli.github.com/
    echo   2. Instale
    echo   3. Execute: gh auth login
    echo   4. Execute este script novamente
    echo.
    echo OPÇÃO 2: Criar manualmente no navegador
    echo   1. Abra: https://github.com/new
    echo   2. Nome: comex-analyzer
    echo   3. Clique em Create repository
    echo   4. Depois execute: CONECTAR_REPOSITORIO_EXISTENTE.bat
    echo.
    pause
    exit /b 0
)

echo ✅ GitHub CLI encontrado
echo.

REM Verificar se está autenticado
gh auth status >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Não está autenticado no GitHub CLI
    echo.
    echo Fazendo login...
    gh auth login
    if errorlevel 1 (
        echo ❌ Falha no login
        pause
        exit /b 1
    )
)

echo ✅ Autenticado no GitHub
echo.

REM Perguntar nome do repositório
set REPO_NAME=comex-analyzer
echo Nome do repositório (Enter para usar: comex-analyzer):
set /p REPO_NAME=
if "%REPO_NAME%"=="" set REPO_NAME=comex-analyzer

echo.
echo Criando repositório: %REPO_NAME%
echo.

REM Criar repositório no GitHub
gh repo create %REPO_NAME% --public --source=. --remote=origin --push
if errorlevel 1 (
    echo.
    echo ❌ Erro ao criar repositório
    echo.
    echo Possíveis causas:
    echo - Repositório com esse nome já existe
    echo - Problema de autenticação
    echo.
    echo Tente criar manualmente em: https://github.com/new
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ REPOSITÓRIO CRIADO COM SUCESSO!
echo ============================================================
echo.
echo URL: https://github.com/%USERNAME%/%REPO_NAME%
echo.
echo Próximos passos:
echo 1. Acesse a URL acima para verificar
echo 2. Siga o PASSO_A_PASSO_DEPLOY.md para fazer deploy
echo.
pause

