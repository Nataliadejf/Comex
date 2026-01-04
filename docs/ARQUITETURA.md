# Arquitetura do Sistema - Comex Analyzer

## Visão Geral

O Comex Analyzer é uma aplicação desktop híbrida composta por:

1. **Backend**: API REST em Python (FastAPI)
2. **Frontend**: Aplicação desktop em Electron + React
3. **Banco de Dados**: SQLite (local)

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Electron)                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │         React Application (UI Components)         │  │
│  │  - Dashboard                                      │  │
│  │  - Busca Avançada                                 │  │
│  │  - Análise por NCM                                │  │
│  └───────────────────────────────────────────────────┘  │
│                      │                                    │
│                      │ HTTP/REST                          │
└──────────────────────┼────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              API Endpoints                         │  │
│  │  - /dashboard/stats                               │  │
│  │  - /buscar                                        │  │
│  │  - /ncm/{ncm}/analise                             │  │
│  │  - /coletar-dados                                 │  │
│  │  - /export/*                                      │  │
│  └───────────────────────────────────────────────────┘  │
│                      │                                    │
│  ┌───────────────────┼─────────────────────────────────┐  │
│  │ Data Collector    │ Business Logic                  │  │
│  │ - API Client     │ - Queries                       │  │
│  │ - Scraper        │ - Aggregations                  │  │
│  │ - Transformer    │ - Validations                   │  │
│  └──────────────────┼─────────────────────────────────┘  │
│                      │                                    │
└──────────────────────┼────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Database (SQLite)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Tables                                │  │
│  │  - operacoes_comex                                │  │
│  │  - ncm_info                                       │  │
│  │  - coleta_log                                     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         External Data Sources                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Portal Comex Stat                                │  │
│  │  - API (se disponível)                            │  │
│  │  - Web Scraping (fallback)                        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Componentes Principais

### Backend

#### 1. API Layer (`main.py`)
- Endpoints REST usando FastAPI
- Validação de dados com Pydantic
- Tratamento de erros
- CORS configurado para Electron

#### 2. Data Collector (`data_collector/`)
- **API Client**: Consome API oficial do Comex Stat (se disponível)
- **Scraper**: Download automatizado via Selenium (fallback)
- **Transformer**: Converte dados brutos para formato do banco
- **Collector**: Orquestra o processo de coleta

#### 3. Database Layer (`database/`)
- **Models**: Definição das tabelas (SQLAlchemy ORM)
- **Database**: Configuração e inicialização do banco
- Índices otimizados para consultas frequentes

#### 4. Business Logic
- Agregações e cálculos
- Filtros e buscas
- Análises estatísticas

#### 5. Utilities (`utils/`)
- **Export**: Exportação para Excel, CSV, PDF
- **Scheduler**: Agendamento de atualizações automáticas

### Frontend

#### 1. Layout (`components/Layout/`)
- Menu lateral (Sider)
- Header com ações
- Layout responsivo

#### 2. Pages (`pages/`)
- **Dashboard**: Métricas e gráficos principais
- **BuscaAvancada**: Filtros e resultados
- **AnaliseNCM**: Análise detalhada por NCM

#### 3. Services (`services/`)
- Cliente HTTP (Axios)
- Endpoints da API
- Tratamento de erros

#### 4. Electron (`public/`)
- Processo principal
- Preload script
- Configuração de build

## Fluxo de Dados

### Coleta de Dados

```
1. Usuário clica em "Coletar Dados"
   ↓
2. Frontend → POST /coletar-dados
   ↓
3. Backend → DataCollector.collect_recent_data()
   ↓
4. Tentar API oficial
   ├─ Sucesso → Transformar dados → Salvar no banco
   └─ Falha → Usar Scraper
       ↓
5. Scraper baixa arquivos CSV
   ↓
6. Parser processa arquivos
   ↓
7. Transformer converte para formato do banco
   ↓
8. Salvar no banco (com verificação de duplicatas)
   ↓
9. Retornar estatísticas para o frontend
```

### Busca de Dados

```
1. Usuário preenche filtros
   ↓
2. Frontend → POST /buscar com filtros
   ↓
3. Backend aplica filtros na query SQL
   ↓
4. Paginação aplicada
   ↓
5. Resultados retornados ao frontend
   ↓
6. Frontend exibe tabela com resultados
```

### Análise por NCM

```
1. Usuário busca por NCM
   ↓
2. Frontend → GET /ncm/{ncm}/analise
   ↓
3. Backend executa múltiplas queries:
   - Estatísticas gerais
   - Principais países
   - Evolução temporal
   ↓
4. Dados agregados retornados
   ↓
5. Frontend exibe gráficos e tabelas
```

## Estrutura de Dados

### OperacaoComex

Campos principais:
- `ncm`: Código NCM (8 dígitos)
- `tipo_operacao`: Importação ou Exportação
- `pais_origem_destino`: País
- `uf`: Unidade Federativa
- `valor_fob`: Valor FOB em USD
- `peso_liquido_kg`: Peso líquido
- `data_operacao`: Data da operação
- `mes_referencia`: Mês de referência (YYYY-MM)

### Índices

Índices criados para otimização:
- `idx_ncm_tipo_data`: NCM + Tipo + Data
- `idx_pais_tipo_data`: País + Tipo + Data
- `idx_uf_tipo_data`: UF + Tipo + Data
- `idx_mes_tipo`: Mês + Tipo

## Segurança

### Atual
- CORS configurado para Electron
- Validação de entrada com Pydantic
- Sanitização de queries SQL (SQLAlchemy ORM)

### Recomendações para Produção
- Autenticação (JWT ou OAuth)
- Rate limiting
- HTTPS
- Validação de arquivos de entrada
- Logs de auditoria

## Performance

### Otimizações Implementadas
- Índices no banco de dados
- Paginação de resultados
- Limite de registros em exportações
- Cache de consultas frequentes (futuro)

### Limitações
- SQLite pode ter limitações com grandes volumes
- Scraping pode ser lento dependendo do site
- Exportações limitadas a 10.000 registros

## Escalabilidade

### Atual
- Aplicação desktop local
- Banco de dados SQLite
- Adequado para uso individual/small team

### Futuro (se necessário)
- Migração para PostgreSQL
- API centralizada
- Múltiplos usuários
- Cache distribuído (Redis)
- Processamento assíncrono (Celery)

## Manutenibilidade

- Código modular e organizado
- Type hints em Python
- Documentação inline
- Separação de responsabilidades
- Testes unitários (a implementar)

