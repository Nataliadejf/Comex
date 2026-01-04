# 🎨 Visualização do Projeto Comex Analyzer

## 🌐 Acessos Disponíveis

### 1. Frontend (Interface Principal)
**URL**: http://localhost:3000

#### Páginas Disponíveis:

##### 📊 Dashboard (`/`)
- **Cards de Métricas**:
  - Volume total de importações (últimos 3 meses)
  - Volume total de exportações (últimos 3 meses)
  - Valor total movimentado (USD)
  - Total de operações

- **Gráficos Interativos**:
  - 📈 Evolução temporal (linha) - Registros por mês
  - 📊 Distribuição por NCM (pizza) - Top 10 NCMs
  - 🌍 Principais países parceiros (barras) - Top 10 países
  - 📉 Comparativo importação vs exportação

- **Tabelas**:
  - Top 10 NCMs por valor
  - Top 10 países por volume

##### 🔍 Busca Avançada (`/busca`)
- **Filtros Disponíveis**:
  - NCM (com autocomplete)
  - Período (data início/fim)
  - Tipo de operação (Importação/Exportação)
  - País
  - UF (Unidade Federativa)
  - Via de transporte
  - Faixa de valor FOB
  - Faixa de peso

- **Resultados**:
  - Tabela paginada com resultados
  - Exportação para Excel/CSV/PDF
  - Filtros aplicados visíveis

##### 📈 Análise por NCM (`/ncm/:ncm`)
- **Estatísticas do NCM**:
  - Total de operações
  - Valor total movimentado
  - Peso total
  - Valor médio por operação

- **Análises**:
  - Principais importadores/exportadores
  - Evolução temporal de preços
  - Sazonalidade
  - Variação de volume
  - Custo médio de frete por via

### 2. Backend API
**URL**: http://localhost:8000

#### Documentação Interativa:

##### Swagger UI (`/docs`)
- Interface visual completa
- Teste de endpoints diretamente
- Ver schemas de requisição/resposta
- Exemplos de uso

##### ReDoc (`/redoc`)
- Documentação alternativa
- Visualização mais limpa
- Melhor para leitura

#### Endpoints Principais:

```
GET  /health                    - Health check
GET  /dashboard/stats           - Estatísticas do dashboard
POST /buscar                    - Busca avançada
GET  /ncm/{ncm}/analise         - Análise por NCM
POST /export/excel              - Exportar para Excel
POST /export/csv                - Exportar para CSV
POST /export/pdf                - Exportar para PDF
POST /coletar-dados             - Iniciar coleta de dados
```

## 🎯 O Que Você Pode Fazer Agora

### 1. Explorar o Dashboard
- Veja métricas principais
- Analise gráficos interativos
- Identifique principais NCMs e países

### 2. Fazer Buscas
- Use filtros avançados
- Encontre operações específicas
- Exporte resultados

### 3. Analisar NCMs
- Digite um código NCM
- Veja análise detalhada
- Entenda tendências

### 4. Testar a API
- Acesse `/docs`
- Teste endpoints
- Veja respostas em tempo real

## 📸 Screenshots Esperados

### Dashboard
- Cards coloridos com métricas
- Gráficos interativos (Recharts)
- Tabelas com dados ordenáveis
- Layout responsivo (Ant Design)

### Busca Avançada
- Formulário com múltiplos filtros
- Botões de ação (Buscar, Limpar, Exportar)
- Tabela de resultados paginada
- Indicadores de carregamento

### Análise NCM
- Cards com estatísticas
- Gráficos de evolução
- Tabelas de países/UF
- Visualizações de tendências

## 🎨 Design e UX

- **Framework UI**: Ant Design
- **Gráficos**: Recharts
- **Cores**: Tema profissional azul/verde
- **Layout**: Responsivo e moderno
- **Navegação**: Menu lateral fixo
- **Feedback**: Loading states e mensagens de erro

## 💡 Dicas de Navegação

1. **Primeira vez**: Comece pelo Dashboard
2. **Buscar dados**: Use a busca avançada
3. **Analisar produto**: Digite um NCM conhecido
4. **Exportar**: Use os botões de exportação
5. **API**: Explore `/docs` para entender a API

## 🔧 Se Algo Não Estiver Funcionando

1. **Verifique os servidores**:
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000

2. **Verifique os dados**:
   - Execute `python scripts/process_files.py`
   - Verifique se há dados no banco

3. **Verifique os logs**:
   - Backend: Console do PowerShell
   - Frontend: Console do navegador (F12)
   - Logs: `D:\NatFranca\logs\`

## 🎉 Aproveite!

O projeto está completo e funcional. Explore todas as funcionalidades!



