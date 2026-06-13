# Endpoints — Empresas & Contatos

## Tabelas BigQuery usadas

| Tabela BQ | Uso |
|---|---|
| `empresas_base` | CNPJ raiz + razão social para autocomplete |
| `Estabelecimentos_Ativos_UltimoMes` | Filiais, CNAE, telefone, email, UF, município, situação |
| `empresas_ncm_import_export_uf` | FOB e peso por empresa×NCM×UF |
| `importacao_uf_ncm` / `exportacao_uf_ncm` | Fallback agregado por UF×NCM |
| CNAE (carregado do Excel em memória no startup) | Enriquecimento: setor/segmento/ramo/categoria |

---

## 1. GET /api/contatos/autocomplete

Busca rápida por razão social ou CNPJ.

### Query params
| Param | Tipo | Descrição |
|---|---|---|
| `q` | string | Texto livre ou CNPJ |
| `limit` | int | Máx. resultados (padrão 20) |

### Lógica BigQuery
```sql
SELECT cnpj_basico, razao_social, uf_sede, cnae_fiscal_principal
FROM `Projeto_Comex.empresas_base`
WHERE LOWER(razao_social) LIKE LOWER('%{q}%')
   OR CAST(cnpj_basico AS STRING) LIKE '{q}%'
LIMIT {limit}
```

### Response
```json
{
  "items": [
    {
      "cnpj": "33000167000101",
      "razao_social": "VALE S.A.",
      "uf": "ES",
      "cnae_fiscal": "710100",
      "cnae_descricao": "Extração de minério de ferro"
    }
  ]
}
```

---

## 2. GET /api/contatos/empresa/{cnpj}

Perfil completo de uma empresa: dados RF + estabelecimentos + CNAE + comex.

### Path param
- `cnpj`: CNPJ de 14 dígitos (com ou sem formatação)

### Lógica (queries em paralelo)

#### Q1 — Perfil (empresas_base)
```sql
SELECT cnpj_basico, razao_social, natureza_juridica, porte,
       uf_sede, municipio_sede, situacao, data_abertura, cnae_fiscal_principal
FROM `Projeto_Comex.empresas_base`
WHERE cnpj_basico = '{cnpj_raiz}'
LIMIT 1
```

#### Q2 — Estabelecimentos (Estabelecimentos_Ativos_UltimoMes)
```sql
SELECT cnpj_completo, uf, municipio, cnae_fiscal,
       ddd_telefone_1, telefone_1, email, situacao_cadastral
FROM `Projeto_Comex.Estabelecimentos_Ativos_UltimoMes`
WHERE cnpj_basico = '{cnpj_raiz}'
ORDER BY uf, municipio
```

#### Q3 — Comex por NCM (empresas_ncm_import_export_uf)
```sql
SELECT ncm, tipo, SUM(valor_fob) AS valor_usd, SUM(peso_kg) AS peso_kg
FROM `Projeto_Comex.empresas_ncm_import_export_uf`
WHERE cnpj = '{cnpj}'
GROUP BY ncm, tipo
ORDER BY valor_usd DESC
LIMIT 50
```

#### Q4 — Comex por ano
```sql
SELECT EXTRACT(YEAR FROM data_ref) AS ano, tipo,
       SUM(valor_fob) AS valor
FROM `Projeto_Comex.empresas_ncm_import_export_uf`
WHERE cnpj = '{cnpj}'
GROUP BY ano, tipo
ORDER BY ano
```

### Enriquecimento CNAE (em memória — tabela carregada do Excel no startup)
```python
# cnae_map: dict[str, dict] carregado de NOVO_CNAE.xlsx
cnae_info = cnae_map.get(str(cnae_fiscal_principal), None)
# retorna: { setor, segmento, ramo, categoria, produto, descricao }
```

### Response
```json
{
  "perfil": {
    "cnpj": "33000167000101",
    "razao_social": "VALE S.A.",
    "natureza_juridica": "Sociedade Anônima",
    "porte": "GRANDE",
    "uf_sede": "ES",
    "municipio_sede": "VITORIA",
    "situacao": "ATIVA",
    "data_abertura": "1967-06-01",
    "cnae_fiscal": "710100",
    "cnae_descricao": "Extração de minério de ferro"
  },
  "cnae_info": {
    "setor": "INDÚSTRIA",
    "segmento": "MINERAÇÃO",
    "ramo": "EXTRATIVISMO",
    "categoria": "MINÉRIOS METÁLICOS",
    "produto": null,
    "descricao": "Extração de minério de ferro"
  },
  "estabelecimentos": [
    {
      "cnpj_completo": "33000167000101",
      "uf": "ES",
      "municipio": "VITORIA",
      "cnae_fiscal": "710100",
      "cnae_info": { "setor": "INDÚSTRIA", "segmento": "MINERAÇÃO", "ramo": "EXTRATIVISMO", "categoria": "MINÉRIOS METÁLICOS" },
      "telefone1": "(27) 3333-3333",
      "email": "contato@vale.com",
      "situacao_cadastral": "ATIVA"
    }
  ],
  "ncms": [
    { "ncm": "26011100", "descricao": "Minérios de ferro não aglomerados", "tipo": "EXP", "valor_usd": 12500000000, "peso_kg": 380000000 }
  ],
  "comex_por_ano": [
    { "ano": 2023, "valor_importacao": 500000000, "valor_exportacao": 15000000000 }
  ],
  "kpis": {
    "valor_importacao_usd": 500000000,
    "valor_exportacao_usd": 15000000000,
    "num_ncms": 12,
    "num_paises": 45
  },
  "aviso": null
}
```

---

## 3. GET /api/contatos/empresas (listagem com filtros)

### Query params
| Param | Tipo | Descrição |
|---|---|---|
| `setor` | string | Filtro por SETOR do CNAE (ex.: INDÚSTRIA) |
| `segmento` | string | Filtro por SEGMENTO |
| `uf` | string | UF sede |
| `tem_comex` | bool | Apenas empresas com operações comex |
| `tipo_comex` | string | IMP ou EXP |
| `page` | int | Paginação |
| `size` | int | Itens por página |

---

## Startup: carregamento do CNAE em memória

```python
# main.py ou lifespan
import pandas as pd

CNAE_PATH = "data/NOVO_CNAE.xlsx"  # copiar arquivo para o backend

def load_cnae_map() -> dict:
    df = pd.read_excel(CNAE_PATH, dtype={"CNAE": str})
    return {
        str(row["CNAE"]).strip(): {
            "setor": row.get("SETOR"),
            "segmento": row.get("SEGMENTO"),
            "ramo": row.get("RAMO"),
            "categoria": row.get("CATEGORIA"),
            "produto": row.get("PRODUTO") if pd.notna(row.get("PRODUTO")) else None,
        }
        for _, row in df.iterrows()
    }

cnae_map: dict = {}  # global, populado no startup
```
