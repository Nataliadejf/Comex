@echo off
chcp 65001 >nul
echo ============================================================
echo PREPARANDO PROJETO PARA DEPLOY
echo ============================================================
echo.

cd /d "%~dp0"

echo 1. Verificando estrutura do projeto...
if not exist "backend\requirements.txt" (
    echo ❌ Arquivo requirements.txt não encontrado!
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ❌ Arquivo package.json não encontrado!
    pause
    exit /b 1
)

echo ✅ Estrutura OK
echo.

echo 2. Verificando arquivos de deploy...
if exist "backend\Dockerfile" (
    echo ✅ Dockerfile encontrado
) else (
    echo ⚠️ Dockerfile não encontrado (opcional)
)

if exist "backend\render.yaml" (
    echo ✅ render.yaml encontrado
) else (
    echo ⚠️ render.yaml não encontrado (opcional)
)

echo.
echo 3. Criando arquivo .gitignore se necessário...
if not exist ".gitignore" (
    echo Criando .gitignore...
    (
        echo venv/
        echo __pycache__/
        echo *.pyc
        echo .env
        echo node_modules/
        echo build/
        echo .DS_Store
    ) > .gitignore
    echo ✅ .gitignore criado
) else (
    echo ✅ .gitignore já existe
)

echo.
echo ============================================================
echo ✅ PREPARAÇÃO CONCLUÍDA!
echo ============================================================
echo.
echo PRÓXIMOS PASSOS PARA DEPLOY:
echo.
echo 1. Escolha uma plataforma:
echo    - Render.com (recomendado)
echo    - Railway.app
echo    - Vercel + Fly.io
echo.
echo 2. Crie conta na plataforma escolhida
echo.
echo 3. Conecte seu repositório Git
echo.
echo 4. Configure variáveis de ambiente:
echo    - DATABASE_URL (fornecido pela plataforma)
echo    - SECRET_KEY (gere uma chave aleatória)
echo    - REACT_APP_API_URL (URL do backend após deploy)
echo.
echo 5. Faça o deploy!
echo.
echo Consulte DEPLOYMENT_GUIDE.md para mais detalhes.
echo.
pause

