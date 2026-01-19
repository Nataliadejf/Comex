# 🔍 Validar Sistema Via API (Sem Shell)

## 🎯 Problema Resolvido

No plano **free do Render**, você **não tem acesso ao Shell**. Por isso, criamos um **endpoint HTTP** para executar a validação completa do sistema!

## ✅ Solução: Endpoint `/validar-sistema`

Agora você pode validar o sistema **diretamente pelo navegador** ou via **curl/Postman**, sem precisar do Shell!

## 🚀 Como Usar

### **MÉTODO 1: Via Navegador (Mais Fácil)** ⭐

1. **Acesse**: `https://seu-backend.onrender.com/validar-sistema`
   - Substitua `seu-backend` pela URL real do seu backend
   - Exemplo: `https://comex-backend-gecp.onrender.com/validar-sistema`

2. **Você verá** um JSON completo com todos os resultados da validação

3. **Para visualizar melhor**, use um formatador JSON:
   - Chrome: Instale extensão "JSON Formatter"
   - Ou use: https://jsonformatter.org/

### **MÉTODO 2: Via Swagger (Recomendado)** ⭐⭐

1. **Acesse**: `https://seu-backend.onrender.com/docs`

2. **Procure pelo endpoint**: `GET /validar-sistema`

3. **Clique em**: "Try it out" → "Execute"

4. **Você verá** o resultado formatado e colorido!

### **MÉTODO 3: Via curl**

```bash
curl https://seu-backend.onrender.com/validar-sistema
```

### **MÉTODO 4: Via Postman**

- **GET** `https://seu-backend.onrender.com/validar-sistema`
- Clique em "Send"

## 📊 O que o Endpoint Retorna

O endpoint retorna um JSON completo com:

```json
{
  "data_validacao": "2026-01-11T21:00:00",
  "bigquery": {
    "conectado": true,
    "credenciais_configuradas": true,
    "teste_query": true,
    "erro": null
  },
  "banco_dados": {
    "conectado": true,
    "tabelas": {
      "operacoes_comex": {
        "existe": true,
        "total_registros": 1234567
      },
      "empresas": {
        "existe": true,
        "total_registros": 10000
      },
      "empresas_recomendadas": {
        "existe": true,
        "total_registros": 0
      }
    },
    "total_registros": {
      "operacoes_comex": 1234567,
      "empresas": 10000,
      "empresas_recomendadas": 0
    },
    "operacoes_detalhes": {
      "importacao": 600000,
      "exportacao": 634567
    },
    "cnpjs_unicos": {
      "importadores": 50000,
      "exportadores": 45000
    }
  },
  "arquivos_csv": {
    "diretorio_existe": true,
    "arquivos_encontrados": [
      {
        "nome": "conjunto-dados.csv",
        "tamanho": 1234567
      }
    ],
    "total_arquivos": 5,
    "csv_downloads": {
      "total": 50,
      "importacoes": 25,
      "exportacoes": 25
    }
  },
  "relacionamentos": {
    "empresas_recomendadas": {
      "total": 0,
      "importadoras": 0,
      "exportadoras": 0,
      "com_cnpj": 0
    },
    "relacionamento_operacoes_empresas": {
      "cnpjs_operacoes": 50000,
      "cnpjs_empresas": 10000,
      "cnpjs_relacionados": 5000,
      "percentual_relacionado": 10.0
    }
  },
  "resumo": {
    "status_geral": "ATENÇÃO",
    "problemas": [
      "Tabela empresas_recomendadas está vazia",
      "Nenhum relacionamento entre operacoes_comex e empresas"
    ],
    "recomendacoes": [
      "Execute script de análise de sinergias",
      "Execute script de análise de sinergias para criar relacionamentos"
    ]
  }
}
```

## 🔍 Interpretando os Resultados

### ✅ Status Geral: "OK"
Tudo funcionando perfeitamente!

### ⚠️ Status Geral: "ATENÇÃO"
Alguns problemas foram encontrados. Veja a lista de `problemas` e `recomendacoes`.

### ❌ Status Geral: "ERRO"
Erro crítico na validação. Verifique os logs do backend.

## 📋 Checklist de Validação

Após acessar o endpoint, verifique:

- [ ] `bigquery.conectado` = `true`
- [ ] `banco_dados.conectado` = `true`
- [ ] `banco_dados.total_registros.operacoes_comex` > 0
- [ ] `banco_dados.total_registros.empresas` > 0
- [ ] `banco_dados.total_registros.empresas_recomendadas` > 0
- [ ] `relacionamentos.relacionamento_operacoes_empresas.cnpjs_relacionados` > 0
- [ ] `resumo.status_geral` = "OK"

## 🔧 Problemas Comuns e Soluções

### Problema: BigQuery não conectado

**Verificar:**
```json
"bigquery": {
  "conectado": false,
  "erro": "..."
}
```

**Solução:**
1. Render Dashboard → `comex-backend` → Environment
2. Adicione: `GOOGLE_APPLICATION_CREDENTIALS_JSON` com o JSON das credenciais
3. Faça deploy novamente

### Problema: Tabela operacoes_comex vazia

**Verificar:**
```json
"banco_dados": {
  "total_registros": {
    "operacoes_comex": 0
  }
}
```

**Solução:**
1. Execute coleta de dados:
   - Via API: `POST /coletar-dados`
   - Ou via Swagger: `POST /coletar-dados` → "Try it out" → "Execute"

### Problema: Tabela empresas_recomendadas vazia

**Verificar:**
```json
"relacionamentos": {
  "empresas_recomendadas": {
    "total": 0
  }
}
```

**Solução:**
1. Execute análise de sinergias:
   - Via API: `POST /dashboard/analisar-sinergias`
   - Ou via Swagger: `POST /dashboard/analisar-sinergias` → "Try it out" → "Execute"

### Problema: Nenhum relacionamento

**Verificar:**
```json
"relacionamento_operacoes_empresas": {
  "cnpjs_relacionados": 0
}
```

**Solução:**
1. Certifique-se que ambas as tabelas têm dados
2. Execute análise de sinergias para criar relacionamentos

## 💡 Dicas

### Visualizar JSON Formatado

**Opção 1: Extensão do Chrome**
- Instale "JSON Formatter" ou "JSON Viewer"

**Opção 2: Site Online**
- Copie o JSON
- Cole em: https://jsonformatter.org/
- Veja formatado e colorido

**Opção 3: Via Swagger**
- Use o Swagger (`/docs`) - já formata automaticamente!

### Salvar Resultados

Você pode salvar o JSON para comparar depois:

```bash
curl https://seu-backend.onrender.com/validar-sistema > validacao_$(date +%Y%m%d_%H%M%S).json
```

## 🎯 Exemplo de Uso Completo

### 1. Acessar Validação

```
https://comex-backend-gecp.onrender.com/validar-sistema
```

### 2. Verificar Resumo

Procure pela seção `resumo`:
```json
"resumo": {
  "status_geral": "ATENÇÃO",
  "problemas": [...],
  "recomendacoes": [...]
}
```

### 3. Seguir Recomendações

Se houver problemas, siga as recomendações listadas.

### 4. Validar Novamente

Após corrigir, acesse o endpoint novamente para confirmar.

## ✅ Vantagens do Endpoint HTTP

- ✅ **Não precisa de Shell** (funciona no plano free)
- ✅ **Acessível pelo navegador**
- ✅ **Pode ser chamado de qualquer lugar**
- ✅ **Resultados em JSON** (fácil de processar)
- ✅ **Disponível no Swagger** (interface visual)

## 🚀 Próximos Passos

1. **Acesse o endpoint** agora mesmo!
2. **Veja os resultados** da validação
3. **Siga as recomendações** se houver problemas
4. **Execute novamente** após corrigir

**URL do seu backend:** `https://comex-backend-gecp.onrender.com`

**Endpoint de validação:** `https://comex-backend-gecp.onrender.com/validar-sistema`
