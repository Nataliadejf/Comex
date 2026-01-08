@echo off
echo ========================================
echo Adicionando campos de empresa ao banco
echo ========================================
echo.

cd backend
python scripts\adicionar_campos_empresas.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Campos adicionados com sucesso!
    echo.
) else (
    echo.
    echo ❌ Erro ao adicionar campos
    echo.
)

pause



