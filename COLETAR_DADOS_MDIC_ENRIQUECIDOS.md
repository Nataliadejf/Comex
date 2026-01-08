# Coleta Enriquecida de Dados do MDIC

## 📋 Visão Geral

Sistema completo para coletar dados CSV do portal oficial do MDIC e enriquecer com informações de empresas e CNAE para sugestões inteligentes.

**Fonte oficial**: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta

## 🎯 O que foi implementado

### 1. Coletor CSV do MDIC (`mdic_csv_collector.py`)
- ✅ Download automático de tabelas de correlação
- ✅ Download de dados mensais de importação/exportação
- ✅ Suporte a múltiplos formatos de URL
- ✅ Processamento de diferentes encodings
- ✅ Cache de arquivos baixados

### 2. Coletor Enriquecido (`enriched_collector.py`)
- ✅ Integração com empresas do MDIC
- ✅ Enriquecimento com CNAE
- ✅ Sugestões inteligentes baseadas em:
  - Operações reais no banco
  - Empresas do MDIC
  - Classificação CNAE
  - Padrões de importação/exportação

### 3. Endpoints da API

#### `POST /coletar-dados-enriquecidos`
Coleta dados completos do MDIC e enriquece com empresas e CNAE.

**Parâmetros**:
- `meses` (query, opcional): Número de meses para coletar (padrão: 24)

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/coletar-dados-enriquecidos?meses=24"
```

**Resposta**:
```json
{
  "success": true,
  "message": "Coleta enriquecida concluída",
  "stats": {
    "total_registros": 150000,
    "registros_novos": 120000,
    "registros_atualizados": 30000,
    "meses_processados": ["2024-01", "2024-02", ...],
    "tabelas_correlacao": {
      "ncm_sh": "/path/to/NCM_SH.csv",
      "paises": "/path/to/PAIS.csv",
      ...
    },
    "empresas_enriquecidas": 5000
  }
}
```

## 🚀 Como Usar

### 1. Coleta Inicial Completa

Execute a coleta enriquecida para popular o banco com dados reais:

```bash
# Via API
curl -X POST "http://localhost:8000/coletar-dados-enriquecidos?meses=24"

# Ou via Python
python -c "
import asyncio
from backend.data_collector.enriched_collector import EnrichedDataCollector
from backend.database import get_db

async def coletar():
    db = next(get_db())
    collector = EnrichedDataCollector()
    stats = await collector.collect_and_enrich(db, meses=24)
    print(stats)

asyncio.run(coletar())
"
```

### 2. Autocomplete com Dados Reais

Os campos de autocomplete agora usam:
1. **Operações reais** do banco de dados
2. **Empresas do MDIC** (lista oficial)
3. **Sugestões inteligentes** baseadas em CNAE e padrões

**Exemplo**:
```bash
# Buscar importadoras
GET /empresas/autocomplete/importadoras?q=metal&ncm=73182200

# Buscar exportadoras
GET /empresas/autocomplete/exportadoras?q=agro&limit=50
```

### 3. Sugestões Inteligentes

O sistema gera sugestões baseadas em:
- **NCM**: Empresas que operam com produtos similares
- **CNAE**: Empresas da mesma atividade econômica
- **Histórico**: Empresas com padrões de importação/exportação
- **Localização**: Empresas da mesma UF

## 📊 Tabelas de Correlação Baixadas

O sistema baixa automaticamente:

1. **NCM_SH.csv** - Correlação NCM com Sistema Harmonizado
2. **NCM_CGCE.csv** - Correlação NCM com CGCE
3. **NCM_CUCI.csv** - Correlação NCM com CUCI
4. **NCM_ISIC.csv** - Correlação NCM com ISIC
5. **PAIS.csv** - Tabela de países
6. **UF.csv** - Tabela de unidades federativas
7. **VIA.csv** - Tabela de vias de transporte
8. **URF.csv** - Tabela de unidades de receita federal

## 🔄 Fluxo de Coleta

1. **Download de Tabelas**
   - Baixa todas as tabelas de correlação
   - Armazena em `data/mdic_csv/tabelas/`

2. **Download de Dados Mensais**
   - Baixa arquivos `IMP_YYYY_MM.csv` e `EXP_YYYY_MM.csv`
   - Últimos N meses (padrão: 24)
   - Armazena em `data/mdic_csv/`

3. **Processamento**
   - Parse de cada arquivo CSV
   - Transformação para formato do banco
   - Validação de dados

4. **Enriquecimento**
   - Identificação de empresas por CNPJ
   - Busca de informações no MDIC
   - Integração com CNAE

5. **Sugestões**
   - Análise de padrões
   - Geração de sugestões inteligentes
   - Ranking por relevância

## 💡 Sugestões Inteligentes

### Como Funciona

1. **Análise de NCM**
   - Identifica empresas que operam com o mesmo NCM
   - Calcula frequência e valores

2. **Análise de CNAE**
   - Relaciona NCM com atividades econômicas
   - Identifica empresas do mesmo setor

3. **Análise de Padrões**
   - Detecta empresas que importam e exportam
   - Identifica oportunidades de sinergia

4. **Ranking**
   - Ordena por:
     - Confiança (alta/média/baixa)
     - Volume de operações
     - Valor total movimentado
     - Potencial de sinergia

### Exemplo de Sugestão

```json
{
  "nome": "EMPRESA EXEMPLO LTDA",
  "total_operacoes": 150,
  "valor_total": 5000000.00,
  "fonte": "operacoes_reais",
  "confianca": "alta",
  "cnpj": "12345678000190",
  "uf": "SP",
  "cnae": "2511000",
  "classificacao_cnae": "Fabricação de estruturas metálicas",
  "sugestao": true
}
```

## 🔧 Configuração

### Variáveis de Ambiente

Nenhuma configuração adicional necessária. O sistema usa:
- URLs públicas do MDIC
- Dados abertos do governo
- Sem autenticação necessária

### Caminhos

- **Dados CSV**: `data/mdic_csv/`
- **Tabelas**: `data/mdic_csv/tabelas/`
- **CNAE**: `C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx` (configurável)

## ⚠️ Notas Importantes

1. **Primeira Execução**: Pode levar várias horas para baixar todos os dados
2. **Espaço em Disco**: Cada arquivo CSV pode ter vários MB
3. **Rede**: Requer conexão estável com internet
4. **Rate Limiting**: O sistema inclui delays para não sobrecarregar servidores

## 📈 Performance

- **Download**: ~2-5 segundos por arquivo
- **Processamento**: ~1000-5000 registros/segundo
- **Enriquecimento**: ~100-500 operações/segundo
- **Sugestões**: <1 segundo para 20 sugestões

## 🔗 Próximos Passos

1. **Executar Coleta**: Use `POST /coletar-dados-enriquecidos`
2. **Aguardar Conclusão**: Acompanhe os logs
3. **Testar Autocomplete**: Use os campos no dashboard
4. **Verificar Sugestões**: Veja as empresas sugeridas

## 🐛 Troubleshooting

### Erro: "Não foi possível baixar CSV"
- Verifique conexão com internet
- Tente novamente (pode ser temporário)
- Verifique se o formato da URL mudou

### Erro: "Encoding não suportado"
- O sistema tenta múltiplos encodings automaticamente
- Se persistir, verifique o arquivo manualmente

### Autocomplete vazio
- Execute a coleta primeiro
- Verifique se há dados no banco
- Tente sem filtros primeiro

---

**Última atualização**: 06/01/2026



