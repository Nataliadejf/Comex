@echo off
echo ============================================================
echo INSTALACAO DO SELENIUM E CHROMEDRIVER
echo ============================================================
echo.

echo 1. Instalando Selenium...
pip install selenium
if errorlevel 1 (
    echo ERRO ao instalar Selenium
    pause
    exit /b 1
)

echo.
echo 2. Instalando webdriver-manager (para ChromeDriver automatico)...
pip install webdriver-manager
if errorlevel 1 (
    echo ERRO ao instalar webdriver-manager
    pause
    exit /b 1
)

echo.
echo ============================================================
echo INSTALACAO CONCLUIDA!
echo ============================================================
echo.
echo O ChromeDriver sera baixado automaticamente na primeira execucao.
echo.
echo Para testar, execute:
echo   python backend\scripts\testar_scraper_automatico.py
echo.
pause


