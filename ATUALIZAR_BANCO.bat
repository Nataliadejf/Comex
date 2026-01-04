@echo off
chcp 65001 >nul
echo ============================================================
echo 🔄 ATUALIZANDO ESTRUTURA DO BANCO DE DADOS
echo ============================================================
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo.
    echo Executando script de atualização...
    echo.
    python scripts\atualizar_tabela_usuarios.py
    echo.
    echo ✅ Atualização concluída!
) else (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute: INSTALAR_DEPENDENCIAS.bat primeiro
)

echo.
pause


