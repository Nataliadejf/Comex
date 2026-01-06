# Dashboard - Sinergias e Sugestões

## 📋 Visão Geral

O Dashboard agora inclui duas novas seções integradas:

1. **Sinergias por Estado** - Análise de importações vs exportações por UF
2. **Sugestões de Empresas** - Empresas com maior potencial de sinergia

## 🎯 Funcionalidades Implementadas

### 1. Sinergias por Estado
- Mapeia importações e exportações por UF
- Calcula índice de sinergia (0-1)
- Mostra sugestões por estado
- Atualização automática via botão

### 2. Sugestões de Empresas
- Lista empresas com maior potencial
- Filtro por tipo (Importação/Exportação)
- Mostra CNAE e classificação
- Sugestões personalizadas por empresa

### 3. Atualizações Automáticas
- **Coleta de Dados**: Diária às 02:00
- **Empresas MDIC**: Semanalmente (domingo 03:00)
- **Relacionamentos**: Diariamente às 03:30
- **Sinergias**: Diariamente às 04:00
- **Atualização Inicial**: 30 segundos após startup

## 🚀 Como Funciona

### No Backend

1. **Scheduler Automático** (`utils/scheduler.py`):
   - Agenda todas as atualizações
   - Executa em background
   - Não bloqueia o servidor

2. **Data Updater** (`utils/data_updater.py`):
   - Atualiza empresas do MDIC
   - Cruza com operações
   - Calcula sinergias
   - Integra com CNAE

3. **Endpoints para Dashboard**:
   - `GET /dashboard/sinergias-estado` - Sinergias por UF
   - `GET /dashboard/sugestoes-empresas` - Sugestões de empresas
   - `POST /atualizar-dados-completos` - Atualização manual

### No Frontend

1. **Carregamento Automático**:
   - Sinergias carregam após 2 segundos
   - Sugestões carregam imediatamente
   - Evita sobrecarga inicial

2. **Componentes Visuais**:
   - Tabelas interativas
   - Filtros e ordenação
   - Botões de atualização
   - Indicadores visuais (tags, cores)

## 📊 Estrutura dos Dados

### Sinergias por Estado
```json
{
  "uf": "SP",
  "importacoes": {
    "total": 15234,
    "valor_total": 50000000.00,
    "peso_total": 1000000.0
  },
  "exportacoes": {
    "total": 12345,
    "valor_total": 45000000.00,
    "peso_total": 800000.0
  },
  "indice_sinergia": 0.9,
  "sugestao": "Estado com alta sinergia..."
}
```

### Sugestões de Empresas
```json
{
  "cnpj": "12345678000190",
  "razao_social": "EMPRESA EXEMPLO LTDA",
  "uf": "SP",
  "importacoes": {"total_operacoes": 50, "valor_total": 1000000.00},
  "exportacoes": {"total_operacoes": 0, "valor_total": 0.0},
  "potencial_sinergia": 0.5,
  "cnae": "2511000",
  "classificacao_cnae": "Fabricação de estruturas metálicas",
  "sugestao": "Empresa importadora - considere exportar..."
}
```

## 🔄 Fluxo de Atualização

### Inicialização do Backend
1. Servidor inicia
2. Scheduler é configurado
3. Após 30 segundos: atualização inicial executa
4. Empresas MDIC são coletadas
5. Relacionamentos são cruzados
6. Sinergias são calculadas

### Atualizações Agendadas
1. **02:00** - Coleta dados do Comex Stat
2. **03:00** (domingo) - Atualiza empresas MDIC
3. **03:30** - Atualiza relacionamentos
4. **04:00** - Atualiza sinergias

### Atualização Manual
- Via botão "Atualizar" no Dashboard
- Via endpoint `POST /atualizar-dados-completos`
- Via Swagger UI

## 💡 Como Usar no Dashboard

### Visualizar Sinergias
1. A seção "Sinergias por Estado" aparece automaticamente
2. Clique em "Carregar Sinergias" se não aparecer
3. Use "Atualizar" para recarregar dados

### Visualizar Sugestões
1. A seção "Sugestões de Empresas" aparece automaticamente
2. Use o filtro "Tipo" para filtrar:
   - **Todos**: Todas as empresas
   - **Importação**: Empresas que só importam
   - **Exportação**: Empresas que só exportam
3. Clique em "Atualizar" para recarregar

### Interpretar Resultados

**Índice de Sinergia (Estado)**:
- **0.7-1.0**: Alta sinergia - estado faz ambos bem
- **0.3-0.7**: Sinergia moderada - potencial de crescimento
- **<0.3**: Baixa sinergia - foco em uma operação

**Potencial Sinergia (Empresa)**:
- **1.0**: Já faz ambos (importação e exportação)
- **0.5**: Só faz uma - potencial para diversificar
- **0.0**: Sem operações registradas

## 🔧 Configuração

### Arquivo CNAE
O sistema procura automaticamente em:
```
C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx
```

### Horários de Atualização
Configurados em `backend/utils/scheduler.py`:
- Coleta: `02:00` (diário)
- Empresas: `03:00` (domingo)
- Relacionamentos: `03:30` (diário)
- Sinergias: `04:00` (diário)

### Limites
- Relacionamentos: 1000 operações por atualização
- Sinergias: 100 empresas por atualização
- Inicialização: limites reduzidos (500/50)

## 📝 Endpoints Disponíveis

### Para o Dashboard
- `GET /dashboard/sinergias-estado?uf=SP` - Sinergias por estado
- `GET /dashboard/sugestoes-empresas?limite=20&tipo=importacao&uf=SP` - Sugestões

### Para Atualização Manual
- `POST /atualizar-dados-completos` - Atualização completa
- `POST /coletar-empresas-mdic?ano=2024` - Coletar empresas
- `POST /carregar-cnae` - Carregar CNAE

## 🎨 Interface do Dashboard

### Seção Sinergias
- Tabela com estados ordenados por índice
- Colunas: UF, Índice, Importações, Exportações, Sugestão
- Botão de atualização

### Seção Sugestões
- Tabela com empresas ordenadas por potencial
- Colunas: Empresa, Potencial, Importações, Exportações, Sugestão
- Tags: UF, CNAE
- Filtro por tipo
- Botão de atualização

## ⚠️ Notas Importantes

1. **Primeira Execução**: Pode levar alguns minutos para coletar empresas MDIC
2. **CNAE Opcional**: Sistema funciona sem CNAE, mas sugestões são melhores com ele
3. **Dados Anonimizados**: Nem todas as empresas podem ser identificadas
4. **Performance**: Atualizações rodam em background para não bloquear

## 🔗 Próximos Passos

1. **Testar no Dashboard**: Acesse e veja as novas seções
2. **Verificar Atualizações**: Acompanhe logs do backend
3. **Ajustar Horários**: Modifique scheduler se necessário
4. **Carregar CNAE**: Execute `POST /carregar-cnae` se ainda não fez

---

**Última atualização**: 06/01/2026

