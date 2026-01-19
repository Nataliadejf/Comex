# 📤 Como Usar Endpoints de Upload

## 🎯 Endpoints Disponíveis

1. **`POST /upload-e-importar-excel`** - Upload e importa arquivo Excel
2. **`POST /upload-e-importar-cnae`** - Upload e importa arquivo CNAE

---

## 📋 Método 1: Via Swagger UI (Recomendado)

### Passo a Passo:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Recarregue a página** (F5 ou Ctrl+R) para garantir que está atualizado
3. **Procure** na lista de endpoints:
   - `POST /upload-e-importar-excel` (na seção **importacao**)
   - `POST /upload-e-importar-cnae` (na seção **importacao**)
4. **Clique em**: "Try it out"
5. **Procure pelo campo de arquivo**:
   - Deve aparecer um campo **"arquivo"** ou **"Choose File"**
   - Se não aparecer, veja Método 2 abaixo
6. **Clique em**: "Choose File" e selecione o arquivo
7. **Clique em**: "Execute"
8. **Aguarde** alguns minutos

### Se o Campo Não Aparecer no Swagger:

Isso pode acontecer devido a limitações do Swagger UI. Use o **Método 2** (curl) que funciona sempre.

---

## 📋 Método 2: Via curl (Sempre Funciona)

### Para Excel:

**PowerShell:**
```powershell
$filePath = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
curl.exe -X POST `
  "https://comex-backend-gecp.onrender.com/upload-e-importar-excel" `
  -H "accept: application/json" `
  -F "arquivo=@$filePath"
```

**CMD:**
```cmd
curl -X POST ^
  "https://comex-backend-gecp.onrender.com/upload-e-importar-excel" ^
  -H "accept: application/json" ^
  -F "arquivo=@C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
```

### Para CNAE:

**PowerShell:**
```powershell
$filePath = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\CNAE.xlsx"
curl.exe -X POST `
  "https://comex-backend-gecp.onrender.com/upload-e-importar-cnae" `
  -H "accept: application/json" `
  -F "arquivo=@$filePath"
```

---

## 📋 Método 3: Via Postman

1. **Método**: POST
2. **URL**: `https://comex-backend-gecp.onrender.com/upload-e-importar-excel`
3. **Body**: Selecione **form-data**
4. **Key**: `arquivo` (tipo: File)
5. **Value**: Selecione o arquivo Excel
6. **Send**

---

## ✅ Verificar se Funcionou

Após fazer upload, valide:

```bash
GET /validar-sistema
```

Verifique se:
- `banco_dados.total_registros.operacoes_comex` > 0 (para Excel)
- `banco_dados.total_registros.cnae_hierarquia` > 0 (para CNAE)

---

## 🐛 Troubleshooting

### Problema: "Arquivo deve ser Excel"

**Solução:**
- Certifique-se de que o arquivo tem extensão `.xlsx` ou `.xls`
- Verifique se o arquivo não está corrompido

### Problema: Swagger não mostra campo de upload

**Solução:**
- Use curl ou Postman (Método 2 ou 3)
- O endpoint funciona mesmo que o Swagger não mostre o campo
- Limpe o cache do navegador e recarregue

### Problema: Timeout

**Solução:**
- Arquivos grandes podem demorar
- Aguarde alguns minutos
- Verifique os logs do Render

---

## 💡 Dica Importante

**O endpoint funciona mesmo que o Swagger não mostre o campo de upload visualmente!**

Use curl ou Postman se o Swagger não mostrar o campo. O endpoint está funcionando corretamente no backend.
