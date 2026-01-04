# Documentação da API - Comex Analyzer

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/health`

Verifica a saúde da API e conexão com banco de dados.

**Resposta:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Coletar Dados

**POST** `/coletar-dados`

Inicia coleta de dados do Comex Stat (últimos 3 meses).

**Resposta:**
```json
{
  "success": true,
  "message": "Coleta de dados concluída",
  "stats": {
    "total_registros": 15000,
    "meses_processados": ["2024-11", "2024-12", "2025-01"],
    "erros": [],
    "usou_api": false
  }
}
```

---

### Dashboard - Estatísticas

**GET** `/dashboard/stats?meses=3`

Retorna estatísticas para o dashboard.

**Parâmetros:**
- `meses` (query, opcional): Número de meses a considerar (padrão: 3)

**Resposta:**
```json
{
  "volume_importacoes": 1500000.50,
  "volume_exportacoes": 2000000.75,
  "valor_total_usd": 50000000.00,
  "principais_ncms": [
    {
      "ncm": "12345678",
      "descricao": "Descrição do produto",
      "valor_total": 1000000.00,
      "total_operacoes": 500
    }
  ],
  "principais_paises": [
    {
      "pais": "China",
      "valor_total": 5000000.00,
      "total_operacoes": 2000
    }
  ],
  "registros_por_mes": {
    "2024-11": 5000,
    "2024-12": 6000,
    "2025-01": 4000
  }
}
```

---

### Buscar Operações

**POST** `/buscar`

Busca operações com filtros avançados.

**Body:**
```json
{
  "ncm": "12345678",
  "data_inicio": "2024-01-01",
  "data_fim": "2024-12-31",
  "tipo_operacao": "Importação",
  "pais": "China",
  "uf": "SP",
  "via_transporte": "MARITIMA",
  "valor_fob_min": 1000.00,
  "valor_fob_max": 100000.00,
  "peso_min": 100.00,
  "peso_max": 10000.00,
  "page": 1,
  "page_size": 100
}
```

**Resposta:**
```json
{
  "total": 1500,
  "page": 1,
  "page_size": 100,
  "total_pages": 15,
  "results": [
    {
      "id": 1,
      "ncm": "12345678",
      "descricao_produto": "Descrição do produto",
      "tipo_operacao": "Importação",
      "pais_origem_destino": "China",
      "uf": "SP",
      "valor_fob": 50000.00,
      "data_operacao": "2024-11-15"
    }
  ]
}
```

---

### Análise por NCM

**GET** `/ncm/{ncm}/analise`

Retorna análise detalhada de um NCM específico.

**Parâmetros:**
- `ncm` (path): Código NCM de 8 dígitos

**Resposta:**
```json
{
  "ncm": "12345678",
  "estatisticas": {
    "total_operacoes": 500,
    "valor_total": 5000000.00,
    "peso_total": 100000.00,
    "valor_medio": 10000.00
  },
  "principais_paises": [
    {
      "pais": "China",
      "tipo_operacao": "Importação",
      "valor_total": 3000000.00
    }
  ],
  "evolucao_temporal": [
    {
      "mes": "2024-11",
      "tipo_operacao": "Importação",
      "valor_total": 1000000.00,
      "quantidade": 100
    }
  ]
}
```

---

### Exportar para Excel

**POST** `/export/excel`

Exporta resultados de busca para Excel.

**Body:**
```json
{
  "filtros": {
    // Mesmos filtros da busca
  }
}
```

**Resposta:**
```json
{
  "success": true,
  "filepath": "D:\\comex_data\\exports\\relatorio_20250101_120000.xlsx",
  "filename": "relatorio_20250101_120000.xlsx",
  "records": 1500
}
```

---

### Exportar para CSV

**POST** `/export/csv`

Exporta resultados de busca para CSV.

**Body:**
```json
{
  "filtros": {
    // Mesmos filtros da busca
  }
}
```

**Resposta:**
```json
{
  "success": true,
  "filepath": "D:\\comex_data\\exports\\relatorio_20250101_120000.csv",
  "filename": "relatorio_20250101_120000.csv",
  "records": 1500
}
```

---

## Códigos de Status HTTP

- `200`: Sucesso
- `400`: Requisição inválida
- `404`: Recurso não encontrado
- `500`: Erro interno do servidor

## Tratamento de Erros

Todas as respostas de erro seguem o formato:

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

## Autenticação

Atualmente, a API não requer autenticação. Em produção, recomenda-se implementar autenticação adequada.

