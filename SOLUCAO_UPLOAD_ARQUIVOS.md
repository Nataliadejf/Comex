# 📤 Solução: Upload de Arquivos para Render

## ❌ Problema Identificado

Os arquivos Excel estão apenas no computador local e não estão no servidor Render, por isso os endpoints automáticos não encontram os arquivos.

## ✅ Solução: Endpoints de Upload

Criei novos endpoints que permitem fazer **upload direto dos arquivos** via HTTP:

---

## 📁 Endpoint: Upload e Importar Excel

### `POST /upload-e-importar-excel`

Este endpoint permite fazer upload de um arquivo Excel diretamente e importa automaticamente.

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /upload-e-importar-excel`
3. **Clique em**: "Try it out"
4. **Clique em**: "Choose File" e selecione o arquivo Excel
5. **Clique em**: "Execute"
6. **Aguarde** alguns minutos

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/upload-e-importar-excel' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'arquivo=@C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx'
```

**O que este endpoint faz:**
- ✅ Recebe arquivo Excel via upload
- ✅ Salva temporariamente no servidor
- ✅ Lê e processa todas as linhas
- ✅ Importa dados de importação e exportação
- ✅ Remove arquivo temporário após processar
- ✅ Retorna estatísticas detalhadas

---

## 📋 Endpoint: Upload e Importar CNAE

### `POST /upload-e-importar-cnae`

Este endpoint permite fazer upload de um arquivo CNAE Excel diretamente.

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /upload-e-importar-cnae`
3. **Clique em**: "Try it out"
4. **Clique em**: "Choose File" e selecione o arquivo CNAE.xlsx
5. **Clique em**: "Execute"

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/upload-e-importar-cnae' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'arquivo=@C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\CNAE.xlsx'
```

---

## 🎯 Ordem Recomendada de Execução

1. ✅ **Upload Excel** → `POST /upload-e-importar-excel` (selecione arquivo via Swagger)
2. ✅ **Upload CNAE** → `POST /upload-e-importar-cnae` (selecione arquivo via Swagger)
3. ✅ **Configurar BigQuery** → Siga `CONFIGURAR_BIGQUERY_RENDER.md`
4. ✅ **Coletar empresas** → `POST /coletar-empresas-bigquery-ultimos-anos`
5. ✅ **Enriquecer dados** → `POST /enriquecer-com-cnae-relacionamentos`
6. ✅ **Validar resultados** → `GET /validar-sistema`

---

## 💡 Vantagens do Upload

- ✅ **Não precisa ter arquivos no servidor**
- ✅ **Upload direto do computador local**
- ✅ **Mais rápido e conveniente**
- ✅ **Funciona imediatamente após deploy**

---

## 📝 Endpoints Disponíveis

### Upload (Recomendado para arquivos locais):
- **`POST /upload-e-importar-excel`** ⭐ NOVO - Upload e importa Excel
- **`POST /upload-e-importar-cnae`** ⭐ NOVO - Upload e importa CNAE

### Importação Automática (Para arquivos já no servidor):
- **`POST /importar-excel-automatico`** - Importa arquivos do servidor
- **`POST /importar-cnae-automatico`** - Importa CNAE do servidor

**Use os endpoints de upload se os arquivos estão apenas no seu computador!**

---

## 🐛 Troubleshooting

### Problema: "Arquivo deve ser Excel"

**Solução:**
- Certifique-se de que o arquivo tem extensão `.xlsx` ou `.xls`
- Verifique se o arquivo não está corrompido

### Problema: Timeout durante upload

**Solução:**
- Arquivos muito grandes podem demorar
- Aguarde alguns minutos
- Verifique os logs do Render para ver o progresso

### Problema: Erro ao processar arquivo

**Solução:**
- Verifique se o arquivo tem as colunas esperadas
- Verifique os logs do endpoint para ver erros específicos
- Tente com um arquivo menor primeiro para testar

---

## ✅ Próximos Passos

Após fazer upload dos arquivos:

1. Valide com `GET /validar-sistema`
2. Configure BigQuery
3. Colete empresas
4. Enriqueça dados
5. Teste o dashboard
