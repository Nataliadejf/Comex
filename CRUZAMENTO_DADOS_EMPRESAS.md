# Sistema de Cruzamento de Dados com Empresas

## 📋 Visão Geral

Este sistema integra dados do Comex Stat com a **Lista de Empresas Exportadoras e Importadoras do MDIC**, permitindo identificar empresas por CNPJ e nome, mesmo que os dados públicos sejam parcialmente anonimizados.

## 🔍 Limitações dos Dados Públicos

### O que está disponível publicamente:
- ✅ Volume por NCM (Comex Stat)
- ✅ Frete médio por NCM
- ✅ Portos e municípios de origem/destino
- ✅ Lista geral de empresas (MDIC) - **com CNPJ mas sem detalhamento por NCM**

### O que NÃO está disponível publicamente:
- ❌ NCM específico por empresa (sigilo fiscal)
- ❌ Valores exatos por empresa (apenas faixas)
- ❌ Detalhamento completo operação-empresa

## 🎯 O que o Sistema Faz

### 1. Coleta Lista de Empresas do MDIC
- Baixa lista anual de empresas exportadoras e importadoras
- Extrai: CNPJ, Razão Social, Nome Fantasia, UF, Município, Faixa de Valor
- Cria índice por CNPJ para busca rápida

### 2. Cruzamento de Dados
- Tenta identificar empresas nas operações por:
  - **CNPJ direto** (alta confiança) - se disponível nos dados
  - **Razão Social** (confiança média) - busca parcial por nome
- Enriquece operações com dados da empresa quando identificada

### 3. Estatísticas de Cruzamento
- Taxa de identificação de empresas
- Nível de confiança (alta/média/baixa)
- Empresas únicas identificadas

## 🚀 Como Usar

### 1. Coletar Lista de Empresas do MDIC

**Via Endpoint:**
```bash
POST /coletar-empresas-mdic?ano=2024
```

**Via Python:**
```python
from data_collector.empresas_mdic_scraper import EmpresasMDICScraper

scraper = EmpresasMDICScraper()
empresas = await scraper.coletar_empresas(ano=2024)
```

**Via Swagger:**
1. Acesse: `https://comex-backend-wjco.onrender.com/docs`
2. Procure por `POST /coletar-empresas-mdic`
3. Execute com `ano` opcional

### 2. Cruzar Dados de Operações com Empresas

**Via Endpoint:**
```bash
POST /cruzar-dados-empresas
Body: {
  "ncm": "86079900",
  "tipo_operacao": "Importação",
  "uf": "SP",
  "limite": 1000
}
```

**Via Python:**
```python
from data_collector.cruzamento_dados import CruzamentoDados

cruzamento = CruzamentoDados()
resultados = await cruzamento.cruzar_operacoes_bulk(
    db,
    filtros={"ncm": "86079900"},
    limite=1000
)
```

### 3. Ver Estatísticas de Cruzamento

**Via Endpoint:**
```bash
GET /estatisticas-cruzamento
```

## 📊 Estrutura dos Dados

### Lista de Empresas do MDIC
```json
{
  "cnpj": "12345678000190",
  "razao_social": "EMPRESA EXEMPLO LTDA",
  "nome_fantasia": "Exemplo",
  "uf": "SP",
  "municipio": "São Paulo",
  "tipo_operacao": "Exportação",
  "faixa_valor": "US$ 1mi - US$ 5mi",
  "ano": "2024"
}
```

### Resultado do Cruzamento
```json
{
  "operacao": {
    "id": 123,
    "ncm": "86079900",
    "tipo_operacao": "Importação",
    "valor_fob": 50000.00,
    "peso_liquido_kg": 1000.0,
    "pais": "China",
    "uf": "SP",
    "data": "2024-01-15"
  },
  "empresa_identificada": true,
  "empresa_dados": {
    "cnpj": "12345678000190",
    "razao_social": "EMPRESA EXEMPLO LTDA",
    "nome_fantasia": "Exemplo",
    "uf": "SP",
    "municipio": "São Paulo",
    "faixa_valor": "US$ 1mi - US$ 5mi"
  },
  "confianca": "alta"
}
```

## ⚠️ Limitações e Considerações

### 1. Anonimização dos Dados
- Dados públicos do Comex Stat são **anonimizados**
- CNPJ pode não estar disponível em todas as operações
- Razão social pode estar parcialmente oculta

### 2. Lista do MDIC
- Lista é **anual** e pode ter atraso
- Não detalha NCM específico por empresa
- Apenas faixas de valor (não valores exatos)

### 3. Taxa de Identificação
- Depende da disponibilidade de CNPJ/razão social nos dados
- Pode variar entre 10-50% dependendo da fonte
- Identificação por nome tem confiança menor

### 4. Dados da Receita Federal
- **Não estão disponíveis publicamente**
- Requerem acesso via Portal Único Siscomex (certificado digital)
- Ou uso de plataformas privadas pagas

## 💡 Alternativas e Próximos Passos

### 1. Portal Único Siscomex
- Requer certificado digital
- Acesso apenas aos próprios dados ou de clientes com procuração
- Dados completos e não anonimizados

### 2. Plataformas Privadas
- Logcomex, ImportGenius, Panjiva
- Cruzam dados de múltiplas fontes (portos, transportadoras, BL)
- Custo alto, voltado para prospecção

### 3. Melhorias Possíveis
- Integração com APIs de consulta CNPJ (ReceitaWS, etc.)
- Enriquecimento com dados de portos
- Análise de padrões para inferência de empresas

## 🔗 Fontes de Dados

1. **Comex Stat (MDIC)**
   - URL: https://comexstat.mdic.gov.br
   - Dados: Operações anonimizadas por NCM

2. **Lista de Empresas (MDIC)**
   - URL: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/empresas-exportadoras-e-importadoras
   - Dados: CNPJ, nome, faixas de valor

3. **Bases de Dados Brutas**
   - URL: https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/
   - Dados: CSV com operações detalhadas

## 📝 Exemplo Completo

```python
# 1. Coletar empresas do MDIC
scraper = EmpresasMDICScraper()
empresas = await scraper.coletar_empresas(ano=2024)

# 2. Cruzar operações
cruzamento = CruzamentoDados()
resultados = await cruzamento.cruzar_operacoes_bulk(
    db,
    filtros={"ncm": "86079900", "tipo_operacao": "Importação"},
    limite=1000
)

# 3. Ver estatísticas
stats = cruzamento.estatisticas_cruzamento(resultados)
print(f"Taxa de identificação: {stats['taxa_identificacao']:.1f}%")
print(f"Empresas únicas: {stats['empresas_unicas']}")
```

---

**Última atualização**: 06/01/2026



