# projeto_comex

Instruções rápidas para rodar e deploy no Render

Variáveis de ambiente necessárias (Render / .env):

- `GOOGLE_APPLICATION_CREDENTIALS_JSON` — JSON completo da service account do GCP (string). Marque como secret.
- `DATABASE_URL` — URL completa do Postgres (ex: `postgres://user:pass@host:5432/dbname`). Opcionalmente, você pode usar as variáveis abaixo em vez da URL:
  - `DATABASE_HOST`
  - `DATABASE_NAME`
  - `DATABASE_USER`
  - `DATABASE_PASSWORD`
- `SECRET_KEY` — chave secreta do Flask (marcar como secret).
- `GCP_PROJECT` — opcional; usado se quiser sobrescrever o project do BigQuery.
- `PORT` — Render define automaticamente; não é obrigatório localmente.

Como funciona o deploy no Render

1. Configure as Environment Variables no painel do seu serviço (Environment -> Edit).
2. Certifique-se que `GOOGLE_APPLICATION_CREDENTIALS_JSON` contém o JSON inteiro (sem truncamento).
3. Garanta que a tabela `empresas` existe no seu Postgres e que `cnpj` possui constraint UNIQUE ou PRIMARY KEY.
4. O endpoint exposto é `POST /api/coletar-empresas-base-dados`.

Executando localmente

1. Crie um arquivo `.env` com as variáveis acima (ou exporte no seu ambiente).
2. Instale dependências:

```bash
python -m pip install -r requirements.txt
```

3. Rode a aplicação:

```bash
python app.py
```

4. Teste o endpoint:

```bash
curl -X POST http://localhost:5000/api/coletar-empresas-base-dados
```

Observações de produção

- Em produção, não rode com `debug=True`.
- Se o provedor de Postgres exigir SSL, acrescente `?sslmode=require` ao `DATABASE_URL`.
- Considere limitar o número de linhas retornadas do BigQuery ou paginar para evitar custos e timeouts.
# Comex Analyzer

Sistema desktop para análise de dados do comércio exterior brasileiro (Comex Stat).

## 📋 Descrição

Aplicação desktop desenvolvida em Python (FastAPI) + Electron + React para coleta, armazenamento e análise de dados públicos do Portal Comex Stat do MDIC.

## 🚀 Tecnologias

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Frontend**: Electron, React, Recharts, Ant Design
- **Banco de Dados**: SQLite (local)
- **Processamento**: Pandas, NumPy

## 📁 Estrutura do Projeto

```
comex_analyzer/
├── backend/              # API FastAPI
├── frontend/             # Aplicação Electron + React
├── data_collector/       # Módulo de coleta de dados
├── database/             # Modelos e migrações
├── utils/                # Utilitários
├── tests/                # Testes unitários
└── docs/                 # Documentação
```

## 🛠️ Instalação

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## ▶️ Execução

### Backend

```bash
cd backend
python main.py
```

### Frontend

```bash
cd frontend
npm start
```

## 📊 Funcionalidades

- ✅ Coleta automática de dados do Comex Stat
- ✅ Dashboard com métricas principais
- ✅ Busca avançada com múltiplos filtros
- ✅ Análise detalhada por NCM
- ✅ Exportação de relatórios (Excel, CSV, PDF)
- ✅ Gráficos interativos
- ✅ Atualização incremental de dados

## 📚 Documentação

- **[Guia de Instalação](INSTALL.md)** - Instruções detalhadas de instalação
- **[Início Rápido](QUICKSTART.md)** - Comece em 5 minutos
- **[Documentação da API](docs/API.md)** - Referência completa da API
- **[Arquitetura](docs/ARQUITETURA.md)** - Visão técnica do sistema
- **[Changelog](CHANGELOG.md)** - Histórico de versões

## 🎯 Funcionalidades Principais

### 1. Coleta de Dados
- Verificação automática de API oficial do Comex Stat
- Fallback para download automatizado via Selenium
- Coleta dos últimos 3 meses
- Atualização incremental (evita duplicatas)
- Sistema de retry em caso de falha

### 2. Dashboard
- Cards com métricas principais:
  - Volume total de importações/exportações
  - Valor total movimentado (USD)
  - Principais NCMs e países
- Gráficos interativos:
  - Evolução temporal (linha)
  - Distribuição por NCM (pizza)
  - Top países (barras)

### 3. Busca Avançada
- Filtros múltiplos:
  - NCM (8 dígitos)
  - Período (data início/fim)
  - Tipo de operação
  - País
  - UF
  - Via de transporte
  - Faixa de valor FOB
  - Faixa de peso
- Paginação de resultados
- Exportação de resultados

### 4. Análise por NCM
- Estatísticas detalhadas
- Histórico de preços médios
- Principais importadores/exportadores
- Evolução temporal
- Variação de volume

### 5. Exportação
- Excel (.xlsx)
- CSV (.csv)
- PDF (.pdf) - opcional

## 🔒 Segurança e Privacidade

- ✅ Utiliza apenas dados públicos do Portal Comex Stat
- ✅ Não faz scraping de sites privados
- ✅ Dados armazenados localmente
- ✅ Sem envio de dados para servidores externos

## ⚠️ Observações Importantes

### Sobre Logcomex.com
- Este projeto utiliza **apenas** Logcomex.com como referência visual/UX
- **NÃO** faz scraping de dados da Logcomex
- **NÃO** acessa APIs privadas
- **NÃO** baixa arquivos da Logcomex
- Use apenas como inspiração de design

### Portal Comex Stat
- Dados públicos do MDIC
- Estrutura do portal pode mudar (scraper pode precisar ajustes)
- API oficial pode não estar disponível (fallback implementado)

## 🛠️ Desenvolvimento

### Estrutura de Pastas

```
comex_analyzer/
├── backend/                 # Backend Python
│   ├── api/                 # Endpoints da API
│   ├── data_collector/      # Coleta de dados
│   ├── database/            # Modelos e DB
│   ├── utils/               # Utilitários
│   └── main.py              # Aplicação principal
├── frontend/                # Frontend React + Electron
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/           # Páginas principais
│   │   └── services/        # Serviços API
│   └── public/              # Arquivos públicos
├── docs/                    # Documentação
└── D:\comex_data\           # Dados (criado automaticamente)
    ├── raw/                 # Dados brutos
    ├── processed/           # Dados processados
    ├── database/            # Banco SQLite
    ├── exports/             # Relatórios exportados
    └── logs/                # Logs do sistema
```

## 📝 Licença

Este projeto utiliza apenas dados públicos do Portal Comex Stat.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:
1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📧 Suporte

Para questões e suporte, consulte a documentação ou abra uma issue no repositório.

