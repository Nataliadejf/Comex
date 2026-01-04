@echo off
chcp 65001 >nul
echo ============================================================
echo VERIFICANDO PREPARAÇÃO PARA DEPLOY
echo ============================================================
echo.

cd /d "%~dp0"

set ERROS=0

echo 1. Verificando estrutura do projeto...
if not exist "backend\main.py" (
    echo ❌ backend\main.py não encontrado!
    set /a ERROS+=1
) else (
    echo ✅ backend\main.py encontrado
)

if not exist "backend\requirements.txt" (
    echo ❌ backend\requirements.txt não encontrado!
    set /a ERROS+=1
) else (
    echo ✅ backend\requirements.txt encontrado
)

if not exist "frontend\package.json" (
    echo ❌ frontend\package.json não encontrado!
    set /a ERROS+=1
) else (
    echo ✅ frontend\package.json encontrado
)

if not exist "frontend\src" (
    echo ❌ frontend\src não encontrado!
    set /a ERROS+=1
) else (
    echo ✅ frontend\src encontrado
)

echo.
echo 2. Verificando arquivos de deploy...
if exist "backend\Dockerfile" (
    echo ✅ backend\Dockerfile encontrado
) else (
    echo ⚠️ backend\Dockerfile não encontrado (opcional)
)

if exist "backend\render.yaml" (
    echo ✅ backend\render.yaml encontrado
) else (
    echo ⚠️ backend\render.yaml não encontrado (opcional)
)

echo.
echo 3. Verificando .gitignore...
if exist ".gitignore" (
    echo ✅ .gitignore encontrado
) else (
    echo ⚠️ .gitignore não encontrado (recomendado criar)
)

echo.
echo 4. Verificando arquivo .env...
if exist "backend\.env" (
    echo ⚠️ backend\.env encontrado - NÃO commitar no Git!
    echo    Adicione .env ao .gitignore
) else (
    echo ✅ backend\.env não encontrado (correto para Git)
)

if exist "frontend\.env" (
    echo ⚠️ frontend\.env encontrado - Verifique se tem REACT_APP_API_URL
) else (
    echo ℹ️ frontend\.env não encontrado (será criado na Render)
)

echo.
echo 5. Verificando dependências...
if exist "backend\requirements.txt" (
    echo Conteúdo de requirements.txt:
    type backend\requirements.txt | findstr /V "^#" | findstr /V "^$" | findstr /N "."
    echo.
)

echo.
echo ============================================================
if %ERROS% EQU 0 (
    echo ✅ PROJETO PRONTO PARA DEPLOY!
    echo.
    echo Próximos passos:
    echo 1. Criar repositório no GitHub
    echo 2. Fazer upload do código
    echo 3. Criar conta na Render.com
    echo 4. Seguir PASSO_A_PASSO_DEPLOY.md
) else (
    echo ❌ ENCONTRADOS %ERROS% ERRO(S)!
    echo.
    echo Corrija os erros antes de fazer deploy.
)
echo ============================================================
echo.
pause

