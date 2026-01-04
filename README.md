# 🚀 Comex Analyzer - Sistema de Análise de Comércio Exterior

Sistema completo para análise de dados do comércio exterior brasileiro, desenvolvido com Python (FastAPI) e React (Electron).

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Como Popular com Dados](#-como-popular-com-dados)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação](#-documentação)

## ✨ Funcionalidades

### Dashboard Principal
- ✅ Métricas principais (Volume, Valor Total, Operações)
- ✅ Gráficos interativos (Evolução temporal, Top NCMs, Top Países)
- ✅ Filtros avançados (Período, NCM, Tipo, Empresa)
- ✅ Exportação de relatórios (Excel)
- ✅ Design moderno inspirado em Logcomex

### Busca Avançada
- ✅ Filtros múltiplos (NCM, Período, Tipo, País, UF, Via, Valores)
- ✅ Paginação de resultados
- ✅ Exportação de tabelas

### Análise por NCM
- ✅ Histórico de preços médios
- ✅ Principais importadores/exportadores
- ✅ Evolução temporal
- ✅ Variação de volume

## 🛠 Tecnologias

### Backend
- **Python 3.11+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pandas** - Processamento de dados
- **SQLite** - Banco de dados local

### Frontend
- **React 18**
- **Electron** - Aplicação desktop
- **Ant Design** - Componentes UI
- **Recharts** - Gráficos
- **Axios** - Cliente HTTP

## 📦 Instalação

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- npm ou yarn

### Backend

```powershell
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Frontend

```powershell
cd frontend

# Instalar dependências
npm install
```

## 📊 Como Popular com Dados

### Método Recomendado: Download Manual de CSV

1. **Baixe arquivos CSV** do portal Comex Stat:
   - URL: https://comexstat.mdic.gov.br/
   - Arquivos: `EXP_2025.csv` e `IMP_2025.csv`
   - Salve em: `D:\comex\2025\` ou `D:\NatFranca\raw\`

2. **Processe os arquivos**:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python scripts/process_files.py
   ```

3. **Verifique os dados**:
   ```powershell
   python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); print(f'Registros: {db.query(func.count(OperacaoComex.id)).scalar():,}')"
   ```

📖 **Guia completo**: Veja `PASSO_A_PASSO_POPULAR_DADOS.md`

## 🚀 Uso

### Iniciar Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python run.py
```

Backend estará disponível em: **http://localhost:8000**

### Iniciar Frontend

```powershell
cd frontend
npm start
```

Frontend estará disponível em: **http://localhost:3000**

### Acessar Dashboard

Abra o navegador em: **http://localhost:3000**

## 📁 Estrutura do Projeto

```
projeto_comex/
├── backend/
│   ├── main.py                 # Aplicação FastAPI
│   ├── config.py               # Configurações
│   ├── database/               # Modelos e conexão DB
│   ├── data_collector/         # Coleta de dados
│   │   ├── api_client.py      # Cliente API Comex Stat
│   │   ├── transformer.py     # Transformação de dados
│   │   └── collector.py       # Coletor principal
│   ├── scripts/                # Scripts utilitários
│   │   ├── process_files.py   # Processar CSV
│   │   └── recriar_banco.py   # Recriar banco
│   └── utils/                  # Utilitários
├── frontend/
│   ├── src/
│   │   ├── pages/              # Páginas
│   │   │   ├── Dashboard.js   # Dashboard principal
│   │   │   └── BuscaAvancada.js
│   │   ├── components/         # Componentes
│   │   └── services/           # API client
│   └── package.json
└── docs/                        # Documentação
```

## 📖 Documentação

- **`PASSO_A_PASSO_POPULAR_DADOS.md`** - Como popular o dashboard
- **`COMO_POPULAR_DASHBOARD.md`** - Guia completo de coleta de dados
- **`DASHBOARD_LOGCOMEX_STYLE.md`** - Design do dashboard
- **`RESUMO_ALTERACOES.md`** - Histórico de alterações

## 🔧 Configuração

### Variáveis de Ambiente

Crie `.env` na pasta `backend`:

```env
# Diretório de dados
DATA_DIR=D:\NatFranca

# Database
DATABASE_URL=sqlite:///D:/NatFranca/database/comex.db

# API Comex Stat (opcional)
COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
COMEX_STAT_API_KEY=sua_chave_aqui
```

### Frontend

Crie `.env` na pasta `frontend`:

```env
REACT_APP_API_URL=http://localhost:8000
```

## 🎯 Funcionalidades Principais

### Dashboard
- Filtros: Período, NCM, Tipo de Operação, Nome da Empresa
- Métricas: Volume, Valor Total, Operações
- Gráficos: Evolução temporal, Top NCMs, Top Países
- Exportação: Relatório completo em Excel

### Busca Avançada
- Filtros múltiplos com paginação
- Resultados em tabela
- Exportação de dados

### Identificação de Importador/Exportador
- Campos `is_importacao` e `is_exportacao`
- Filtros claros por tipo de operação

## 📊 Banco de Dados

- **Localização**: `D:\NatFranca\database\comex.db`
- **Tipo**: SQLite
- **Tabelas principais**:
  - `operacoes_comex` - Operações de comércio exterior
  - `ncm_info` - Informações sobre NCMs
  - `coleta_log` - Logs de coletas

## 🔄 Scripts Úteis

### Processar Arquivos CSV
```powershell
python scripts/process_files.py
```

### Recriar Banco de Dados
```powershell
python scripts/recriar_banco.py
```

### Adicionar Campos de Identificação
```powershell
python scripts/adicionar_campos_importador_exportador.py
```

## 🐛 Troubleshooting

### Dashboard não carrega dados
1. Verifique se há dados no banco
2. Execute `python scripts/process_files.py`
3. Reinicie o backend

### Erro ao processar CSV
1. Verifique se o arquivo está no formato correto
2. Confirme que está em `D:\comex\2025\` ou `D:\NatFranca\raw\`
3. Verifique logs em `D:\NatFranca\logs\`

### Banco corrompido
```powershell
python scripts/recriar_banco.py
python scripts/process_files.py
```

## 📝 Licença

Este projeto é de uso interno.

## 👥 Autor

Desenvolvido para análise de dados do comércio exterior brasileiro.

---

**Última atualização**: Janeiro 2025
