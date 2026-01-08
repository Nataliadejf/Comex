# Integração com API e CSV Scraper

## ✅ O que foi implementado

### 1. **API Client Atualizado**
- Configurado para usar `https://api-comexstat.mdic.gov.br` por padrão
- Melhor tratamento de erros e fallbacks
- Suporte a diferentes formatos de resposta

### 2. **CSV Scraper (Novo)**
- Baixa arquivos CSV diretamente das bases de dados brutas do MDIC
- URL base: `https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/`
- Formatos suportados:
  - `IMP_YYYY_MM.csv` (Importação)
  - `EXP_YYYY_MM.csv` (Exportação)
- Não requer Selenium ou navegador (funciona no Render)

### 3. **Sistema de Fallback em 3 Níveis**
1. **API REST** (`api-comexstat.mdic.gov.br`) - Primeira tentativa
2. **CSV Scraper** (Bases de dados brutas) - Fallback automático
3. **Scraper Tradicional** (Selenium) - Último recurso (se disponível)

## 🚀 Como usar

### Configurar no Render

1. **Variáveis de Ambiente:**
   ```
   COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
   COMEX_STAT_API_KEY= (deixe vazio se não tiver)
   ```

2. **Coletar Dados:**
   - Via endpoint: `POST /coletar-dados-ncms`
   - O sistema tentará automaticamente:
     1. API REST primeiro
     2. CSV Scraper se API falhar
     3. Scraper tradicional se CSV falhar

### Testar Localmente

```python
# Via script
python backend/scripts/coletar_dados.py

# Via endpoint
POST http://localhost:8000/coletar-dados-ncms
Body: {
  "ncms": null,
  "meses": 24,
  "tipo_operacao": null
}
```

## 📊 Estrutura dos Arquivos CSV

Os arquivos CSV das bases de dados brutas contêm:
- NCM (8 dígitos)
- Descrição do produto
- País de origem/destino
- UF
- Valores (FOB, frete, seguro)
- Pesos (líquido, bruto)
- Empresas (importador/exportador)
- CNPJ (quando disponível)

## 🔍 URLs dos Arquivos CSV

Padrão de URL:
```
https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_2024_01.csv
https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_2024_01.csv
```

O scraper tenta múltiplos formatos automaticamente:
- `IMP_YYYY_MM.csv`
- `IMP_YYYYMM.csv`
- `imp_YYYY_MM.csv`
- `imp_YYYYMM.csv`

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# API (opcional - tentará usar por padrão)
COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
COMEX_STAT_API_KEY= (opcional)

# Diretório de downloads CSV
DATA_DIR=./comex_data
```

### Código

O sistema detecta automaticamente qual método usar:
- Se API disponível → usa API
- Se API falhar → usa CSV scraper
- Se CSV falhar → usa scraper tradicional (se disponível)

## 📝 Logs

O sistema registra:
- Qual método foi usado
- Quantos registros foram coletados
- Erros encontrados
- Arquivos CSV baixados

## 🎯 Próximos Passos

1. **Testar a API real:**
   - Acesse: https://api-comexstat.mdic.gov.br/docs
   - Verifique endpoints disponíveis
   - Configure API key se necessário

2. **Verificar CSV Scraper:**
   - Teste download de um mês específico
   - Verifique formato dos dados
   - Ajuste mapeamento se necessário

3. **Deploy no Render:**
   - Atualize variáveis de ambiente
   - Teste coleta de dados
   - Monitore logs

---

**Última atualização**: 05/01/2026



