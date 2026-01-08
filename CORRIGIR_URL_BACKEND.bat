@echo off
chcp 65001 >nul
echo ============================================================
echo CORREÇÃO DA URL DO BACKEND NO FRONTEND
echo ============================================================
echo.
echo Atualizando frontend\.env para usar:
echo https://comex-tsba.onrender.com
echo.

echo REACT_APP_API_URL=https://comex-tsba.onrender.com > frontend\.env

echo ✅ Arquivo .env atualizado!
echo.
echo Conteúdo do arquivo:
type frontend\.env
echo.
echo ============================================================
echo IMPORTANTE:
echo ============================================================
echo 1. Reinicie o frontend após esta alteração!
echo 2. Execute: INICIAR_FRONTEND.bat
echo 3. Ou: cd frontend ^&^& npm start
echo.
echo Se o backend estiver "dormindo" no Render (plano free):
echo - Aguarde 30-60 segundos após a primeira requisição
echo - Ou faça um "Manual Deploy" no Render Dashboard
echo.
pause


