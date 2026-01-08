# 📊 Script para Carregar Dados Após Deploy

## 🎯 Objetivo

Garantir que após o deploy, os dados de importação/exportação e empresas recomendadas sejam carregados corretamente no dashboard.

## ✅ Dados que Devem Estar Disponíveis

1. **Empresas Recomendadas**: `backend/data/empresas_recomendadas.xlsx`
2. **Resumo ComexStat**: `backend/data/resumo_dados_comexstat.json`
3. **Dados NCM**: `backend/data/dados_ncm_comexstat.json`

## 🔍 Verificação Automática

O backend já está configurado para:
- ✅ Ler `empresas_recomendadas.xlsx` automaticamente
- ✅ Servir dados via endpoints `/dashboard/empresas-recomendadas`
- ✅ Servir empresas importadoras via `/dashboard/empresas-importadoras`
- ✅ Servir empresas exportadoras via `/dashboard/empresas-exportadoras`
- ✅ Servir dados ComexStat via `/dashboard/dados-comexstat`

## 📋 Endpoints Disponíveis

### 1. Empresas Recomendadas
```
GET /dashboard/empresas-recomendadas?limite=100&tipo=importacao
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": [
    {
      "cnpj": "12.345.678/0001-90",
      "razao_social": "Empresa Exemplo LTDA",
      "nome_fantasia": "Exemplo",
      "cnae": "1234-5/67",
      "estado": "SP",
      "endereco": "Rua Exemplo, 123",
      "ncm_relacionado": "12345678",
      "importado_rs": 1000000.00,
      "exportado_rs": 500000.00,
      "capital_social": 500000.00,
      "funcionarios_estimado": 50,
      "peso_participacao": 75.5,
      "sugestao": "cliente potencial"
    }
  ]
}
```

### 2. Empresas Importadoras
```
GET /dashboard/empresas-importadoras?limite=10
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": [
    {
      "pais": "Empresa Importadora LTDA",
      "valor_total": 200000.00,
      "total_operacoes": 1,
      "uf": "SP",
      "peso_participacao": 80.0
    }
  ]
}
```

### 3. Empresas Exportadoras
```
GET /dashboard/empresas-exportadoras?limite=10
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": [
    {
      "pais": "Empresa Exportadora LTDA",
      "valor_total": 150000.00,
      "total_operacoes": 1,
      "uf": "RJ",
      "peso_participacao": 70.0
    }
  ]
}
```

### 4. Dados ComexStat
```
GET /dashboard/dados-comexstat
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": {
    "resumo_importacoes": {
      "total_valor": 1000000000.00,
      "total_operacoes": 5000
    },
    "resumo_exportacoes": {
      "total_valor": 800000000.00,
      "total_operacoes": 3000
    }
  }
}
```

## 🧪 Testar Após Deploy

### 1. Testar Backend

```bash
# Health Check
curl https://[BACKEND_URL]/health

# Empresas Recomendadas
curl https://[BACKEND_URL]/dashboard/empresas-recomendadas?limite=10

# Empresas Importadoras
curl https://[BACKEND_URL]/dashboard/empresas-importadoras?limite=10

# Empresas Exportadoras
curl https://[BACKEND_URL]/dashboard/empresas-exportadoras?limite=10

# Dados ComexStat
curl https://[BACKEND_URL]/dashboard/dados-comexstat
```

### 2. Testar Frontend

1. Acesse: `https://comex-4.onrender.com`
2. Abra o Console do Navegador (F12)
3. Verifique se não há erros de conexão
4. Verifique se os dados estão sendo carregados:
   - Seção "Prováveis Importadores" deve mostrar empresas
   - Seção "Prováveis Exportadores" deve mostrar empresas
   - Cards de estatísticas devem mostrar valores

## 🔧 Se Dados Não Aparecerem

### Problema 1: Arquivo não encontrado

**Sintoma:** Endpoint retorna `{"success": false, "data": []}`

**Solução:**
1. Verifique se o arquivo existe em `backend/data/`
2. Verifique se o arquivo foi commitado no Git
3. Verifique se o arquivo está sendo copiado no build do Render

### Problema 2: Erro de leitura

**Sintoma:** Erro 500 no endpoint

**Solução:**
1. Verifique os logs do backend no Render
2. Verifique se pandas e openpyxl estão instalados
3. Verifique se o formato do arquivo está correto

### Problema 3: Frontend não conecta

**Sintoma:** Erro de conexão no console

**Solução:**
1. Verifique `frontend/.env` - deve ter `REACT_APP_API_URL` correto
2. Rebuild do frontend após alterar `.env`
3. Verifique se o backend está online

## ✅ Checklist Pós-Deploy

- [ ] Backend está online e respondendo
- [ ] Endpoint `/health` retorna OK
- [ ] Endpoint `/dashboard/empresas-recomendadas` retorna dados
- [ ] Endpoint `/dashboard/empresas-importadoras` retorna dados
- [ ] Endpoint `/dashboard/empresas-exportadoras` retorna dados
- [ ] Endpoint `/dashboard/dados-comexstat` retorna dados
- [ ] Frontend está online
- [ ] Dashboard mostra empresas recomendadas
- [ ] Seções "Prováveis Importadores" e "Prováveis Exportadores" aparecem
- [ ] Dados de importação/exportação aparecem nos cards
