# 🚀 Importação Automática de Arquivos

## 🎯 Objetivo

Importar automaticamente todos os arquivos Excel encontrados nas pastas, sem precisar especificar nomes de arquivos manualmente.

---

## 📁 Endpoint: Importar Excel Automaticamente

### `POST /importar-excel-automatico`

Este endpoint procura automaticamente todos os arquivos Excel na pasta `comex_data/comexstat_csv/` e importa todos encontrados.

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /importar-excel-automatico`
3. **Clique em**: "Try it out" → "Execute"
4. **Aguarde** alguns minutos

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/importar-excel-automatico' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**

- ✅ Procura automaticamente arquivos `.xlsx` e `.xls` em:
  - `comex_data/comexstat_csv/` (local)
  - `/opt/render/project/src/comex_data/comexstat_csv/` (Render)
- ✅ Filtra apenas arquivos válidos (ignora arquivos temporários como `~$CNAE.xlsx`)
- ✅ Processa cada arquivo encontrado
- ✅ Importa dados de importação e exportação
- ✅ Evita duplicatas
- ✅ Retorna estatísticas detalhadas por arquivo

**Arquivos que serão importados:**
- `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
- Qualquer outro arquivo Excel que contenha "exportacao", "importacao", "comex" ou "geral" no nome

**Resposta esperada:**
```json
{
  "success": true,
  "message": "Importação automática concluída",
  "stats": {
    "total_arquivos": 1,
    "arquivos_processados": 1,
    "arquivos_com_erro": 0,
    "total_registros": 15000,
    "importacoes": 7500,
    "exportacoes": 7500,
    "detalhes_por_arquivo": [
      {
        "arquivo": "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx",
        "total_registros": 15000,
        "importacoes": 7500,
        "exportacoes": 7500
      }
    ]
  }
}
```

---

## 📋 Endpoint: Importar CNAE Automaticamente

### `POST /importar-cnae-automatico`

Este endpoint procura automaticamente todos os arquivos CNAE na pasta e importa todos encontrados.

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /importar-cnae-automatico`
3. **Clique em**: "Try it out" → "Execute"

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/importar-cnae-automatico' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**

- ✅ Procura automaticamente arquivos CNAE em:
  - `comex_data/comexstat_csv/` (arquivos com "CNAE" no nome)
  - `comex_data/comexstat_csv/cnae/` (pasta específica)
  - `/opt/render/project/src/comex_data/comexstat_csv/` (Render)
- ✅ Processa cada arquivo encontrado
- ✅ Importa hierarquia CNAE (classe, grupo, divisão, seção)
- ✅ Evita duplicatas
- ✅ Retorna estatísticas detalhadas

**Arquivos que serão importados:**
- `CNAE.xlsx`
- `NOVO CNAE.xlsx`
- Qualquer arquivo com "CNAE" no nome

---

## 🎯 Ordem Recomendada de Execução

1. ✅ **Importar Excel automaticamente** → `POST /importar-excel-automatico`
2. ✅ **Importar CNAE automaticamente** → `POST /importar-cnae-automatico`
3. ✅ **Configurar BigQuery** → Siga `CONFIGURAR_BIGQUERY_RENDER.md`
4. ✅ **Coletar empresas** → `POST /coletar-empresas-bigquery-ultimos-anos`
5. ✅ **Enriquecer dados** → `POST /enriquecer-com-cnae-relacionamentos`
6. ✅ **Validar resultados** → `GET /validar-sistema`

---

## 💡 Vantagens da Importação Automática

- ✅ **Não precisa especificar nomes de arquivos**
- ✅ **Processa todos os arquivos encontrados**
- ✅ **Mais rápido e conveniente**
- ✅ **Retorna estatísticas detalhadas por arquivo**
- ✅ **Continua mesmo se um arquivo tiver erro**

---

## 🐛 Troubleshooting

### Problema: Nenhum arquivo encontrado

**Solução:**
- Verifique se os arquivos estão em `comex_data/comexstat_csv/`
- Verifique se os arquivos têm extensão `.xlsx` ou `.xls`
- Verifique se os nomes dos arquivos contêm palavras-chave (exportacao, importacao, comex, geral, CNAE)

### Problema: Arquivo processado mas nenhum registro importado

**Possíveis causas:**
- Arquivo não tem as colunas esperadas
- Dados estão em formato diferente
- Valores estão vazios ou inválidos

**Solução:**
- Verifique os logs do endpoint para ver erros específicos
- Use o endpoint manual (`/importar-excel-manual`) para um arquivo específico e ver detalhes

---

## 📝 Endpoints Disponíveis

### Importação Automática (Recomendado):
- **`POST /importar-excel-automatico`** ⭐ NOVO - Importa todos os arquivos Excel automaticamente
- **`POST /importar-cnae-automatico`** ⭐ NOVO - Importa todos os arquivos CNAE automaticamente

### Importação Manual (Para casos específicos):
- **`POST /importar-excel-manual`** - Importa arquivo específico
- **`POST /importar-cnae`** - Importa arquivo CNAE específico

**Use os endpoints automáticos primeiro!**
