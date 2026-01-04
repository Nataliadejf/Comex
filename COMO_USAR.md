# 🚀 Como Usar o Projeto Comex Analyzer

## 📋 Pré-requisitos

- Python 3.11+
- Node.js 16+
- Banco de dados SQLite (criado automaticamente)

## 🎯 Início Rápido

### 1. Iniciar o Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
python run.py
```

O backend estará disponível em: **http://localhost:8000**

### 2. Iniciar o Frontend

```bash
cd frontend
npm install  # Primeira vez apenas
npm start
```

O frontend estará disponível em: **http://localhost:3000**

## 🌐 Acessos

- **Frontend (Interface Principal)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentação API (Swagger)**: http://localhost:8000/docs
- **Documentação API (ReDoc)**: http://localhost:8000/redoc

## 📊 Funcionalidades Disponíveis

### 1. Dashboard Principal
- Métricas principais (importações/exportações)
- Gráficos interativos
- Principais NCMs e países
- Evolução temporal

### 2. Busca Avançada
- Filtros por NCM, período, tipo de operação
- Filtros por país, UF, via de transporte
- Filtros por valor FOB e peso
- Paginação de resultados

### 3. Análise por NCM
- Histórico de preços médios
- Principais importadores/exportadores
- Sazonalidade
- Variação de volume

### 4. Exportação de Relatórios
- Excel (.xlsx)
- CSV
- PDF

## 🔧 Endpoints da API

### Health Check
```
GET /health
```

### Dashboard Stats
```
GET /dashboard/stats?meses=3
```

### Buscar Operações
```
POST /buscar
Body: {
  "ncm": "12345678",
  "data_inicio": "2024-01-01",
  "data_fim": "2024-12-31",
  "tipo_operacao": "Importação",
  ...
}
```

### Análise por NCM
```
GET /ncm/{ncm}/analise
```

### Exportar Dados
```
POST /export/excel
POST /export/csv
POST /export/pdf
```

## 📥 Coletar Dados

### Opção 1: Sistema Completo Automatizado
```bash
cd backend
python scripts/sistema_completo.py
```

### Opção 2: Processar Arquivos CSV Existentes
```bash
cd backend
python scripts/process_files.py
```

### Opção 3: Baixar Tabela NCM via API
```bash
cd backend
python -c "from data_collector.comex_api_client import ComexStatAPI; api = ComexStatAPI(); api.obter_ncm()"
```

## 📁 Estrutura de Dados

### Localização dos Arquivos
- **Banco de Dados**: `D:\NatFranca\database\comex.db`
- **Arquivos CSV Raw**: `D:\NatFranca\raw\YYYY\`
- **Arquivos Processados**: `D:\NatFranca\processed\`
- **Exportações**: `D:\NatFranca\exports\`
- **Logs**: `D:\NatFranca\logs\`

### Formato dos Arquivos CSV
Coloque os arquivos CSV baixados do portal Comex Stat em:
```
D:\comex\YYYY\EXP_YYYY.csv  (Exportação)
D:\comex\YYYY\IMP_YYYY.csv  (Importação)
```

## 🐛 Solução de Problemas

### Backend não inicia
1. Verifique se a porta 8000 está livre
2. Verifique se o ambiente virtual está ativado
3. Verifique os logs em `D:\NatFranca\logs\`

### Frontend não carrega
1. Verifique se a porta 3000 está livre
2. Execute `npm install` novamente
3. Verifique o console do navegador (F12)

### Dados não aparecem
1. Execute `python scripts/process_files.py` para processar CSV
2. Verifique se há dados no banco: `SELECT COUNT(*) FROM operacoes_comex;`
3. Verifique os logs de processamento

### Erro de conexão com API
1. O sistema usa fallback automático
2. Use download manual de CSV (método mais confiável)
3. Verifique `API_COMEX_STAT.md` para detalhes

## 📚 Documentação Adicional

- `STATUS_FINAL_API.md` - Status da integração com API
- `API_COMEX_STAT.md` - Documentação da API do Comex Stat
- `COMO_BAIXAR_DADOS.md` - Como baixar dados manualmente
- `docs/API.md` - Documentação completa da API do projeto

## 💡 Dicas

1. **Primeira execução**: Execute `sistema_completo.py` para processar dados
2. **Atualização de dados**: Baixe novos CSV e execute `process_files.py`
3. **Performance**: Para arquivos grandes, use `process_single_file.py`
4. **API**: A tabela NCM pode ser baixada automaticamente via API

## 🎉 Pronto para Usar!

O projeto está completo e funcional. Acesse http://localhost:3000 para começar!



