# 🔧 Corrigir: Campos de Upload Não Aparecem no Swagger

## ❌ Problema

Os campos de upload não aparecem no Swagger UI para os endpoints `/upload-e-importar-excel` e `/upload-e-importar-cnae`.

## ✅ Solução Aplicada

Fiz os seguintes ajustes:

1. ✅ Reordenei os parâmetros (db primeiro, arquivo depois)
2. ✅ Adicionei tags para melhor organização no Swagger
3. ✅ Melhorei as descrições dos parâmetros

## 🔍 Como Verificar

### 1. Aguardar Deploy

O código foi commitado. Aguarde 2-5 minutos para o deploy terminar.

### 2. Acessar Swagger

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Recarregue a página** (F5 ou Ctrl+R)
3. **Procure**: `POST /upload-e-importar-excel` na seção **importacao**

### 3. Verificar Campo de Upload

No Swagger, você deve ver:
- Um campo **"Choose File"** ou **"arquivo"**
- Botão para selecionar arquivo
- Descrição: "Arquivo Excel (.xlsx ou .xls) para importar"

## 🐛 Se Ainda Não Aparecer

### Problema: Swagger não mostra campo de upload

**Possíveis causas:**
- Cache do navegador
- Versão do Swagger UI
- Problema com python-multipart

**Soluções:**

1. **Limpar cache do navegador:**
   - Pressione Ctrl+Shift+Delete
   - Limpe cache e cookies
   - Recarregue a página

2. **Acessar diretamente:**
   ```
   https://comex-backend-gecp.onrender.com/docs#/importacao/upload_e_importar_excel_upload_e_importar_excel_post
   ```

3. **Usar curl diretamente** (funciona mesmo sem Swagger):
   ```bash
   curl -X 'POST' \
     'https://comex-backend-gecp.onrender.com/upload-e-importar-excel' \
     -H 'accept: application/json' \
     -H 'Content-Type: multipart/form-data' \
     -F 'arquivo=@C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx'
   ```

## 📝 Endpoints de Upload

1. **`POST /upload-e-importar-excel`** - Upload e importa Excel
2. **`POST /upload-e-importar-cnae`** - Upload e importa CNAE

**Ambos estão na tag "importacao" no Swagger.**

## 💡 Dica

Se o Swagger não mostrar o campo de upload, você pode usar **curl** ou **Postman** diretamente. O endpoint funciona mesmo que o Swagger não mostre o campo visualmente.
