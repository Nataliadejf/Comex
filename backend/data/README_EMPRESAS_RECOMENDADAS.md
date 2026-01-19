# Sistema de Empresas Recomendadas - Comércio Exterior

## Visão Geral

Sistema end-to-end para coletar, organizar e relacionar informações sobre empresas importadoras e exportadoras brasileiras, cruzando dados com a base interna comex e gerando sugestões de clientes/fornecedores potenciais.

## Arquivos Gerados

- **`empresas_recomendadas.xlsx`**: Tabela completa em formato Excel
- **`empresas_recomendadas.csv`**: Tabela completa em formato CSV

## Estrutura da Tabela

A tabela `empresas_recomendadas_comex` contém as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| CNPJ | CNPJ da empresa (formatado ou fictício se dados agregados) |
| Razão Social | Razão social da empresa |
| Nome Fantasia | Nome fantasia (quando disponível) |
| CNAE | CNAE principal da empresa |
| Estado | UF da empresa |
| Endereço | Endereço completo |
| NCM Relacionado | Código NCM relacionado à empresa |
| Descrição NCM | Descrição do produto NCM |
| Importado (R$) | Valor total importado em Reais |
| Exportado (R$) | Valor total exportado em Reais |
| Capital Social | Capital social (quando disponível) |
| Funcionários (Estimado) | Número estimado de funcionários |
| Peso Participação (0-100) | Score calculado (50% import, 40% export, 10% NCMs) |
| Sugestão | CLIENTE_POTENCIAL ou FORNECEDOR_POTENCIAL |
| Dados Estimados | SIM/NÃO - indica se dados foram estimados |

## Como Executar

```bash
cd projeto_comex
python backend/scripts/gerar_empresas_recomendadas.py
```

## Fluxo de Trabalho

### ETAPA 1: COLETA DE DADOS
- Busca empresas no banco de dados interno
- Se não encontrar, busca no arquivo Excel (`H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`)
- Enriquece dados via API ReceitaWS (quando disponível)
- Valida CNPJs
- Remove duplicatas

### ETAPA 2: CÁLCULO DE SCORE (PESO_PARTICIPACAO)
- Calcula score baseado em:
  - 50% volume financeiro importado
  - 40% volume financeiro exportado
  - 10% quantidade de NCMs movimentados
- Normaliza para escala 0-100

### ETAPA 3: CRUZAMENTO COM BASE INTERNA
- Carrega NCMs da base interna comex
- Relaciona empresas aos NCMs que movimentam

### ETAPA 4: GERAÇÃO DE SUGESTÕES
- Identifica empresas que importam determinado NCM = FORNECEDOR_POTENCIAL
- Identifica empresas que exportam determinado NCM = CLIENTE_POTENCIAL
- Ordena por volume de compra/venda

### ETAPA 5: GERAÇÃO DA TABELA FINAL
- Consolida relacionamentos e sugestões
- Formata dados conforme padrão solicitado
- Converte valores USD para BRL (taxa 5.0)

### ETAPA 6: SALVAMENTO
- Salva em Excel (`backend/data/empresas_recomendadas.xlsx`)
- Salva em CSV (`backend/data/empresas_recomendadas.csv`)

## Módulos do Sistema

### `empresa_data_collector.py`
- Coleta dados de empresas
- Valida CNPJs
- Enriquece dados via APIs públicas
- Remove duplicatas

### `empresa_scoring.py`
- Calcula PESO_PARTICIPACAO
- Normaliza scores

### `empresa_cruzamento.py`
- Cruza dados com base interna
- Gera sugestões de clientes/fornecedores

### `gerar_empresas_recomendadas.py`
- Script principal que orquestra todo o fluxo

## Validações Implementadas

- ✅ Validação de CNPJ (dígitos verificadores)
- ✅ Remoção de duplicatas por CNPJ
- ✅ Flag de dados estimados
- ✅ Tratamento de valores nulos
- ✅ Conversão de moedas (USD → BRL)

## Limitações e Melhorias Futuras

- **Dados Estimados**: Quando não há dados reais no banco, o sistema cria empresas agregadas baseadas em UF e NCM
- **API ReceitaWS**: Limitada a 100 chamadas por execução (rate limiting)
- **Funcionários**: Estimado baseado em heurísticas de faturamento
- **Capital Social**: Buscado via API quando disponível

## Próximos Passos Sugeridos

1. Integrar com mais APIs públicas (Serasa, SPC, etc.)
2. Buscar dados de LinkedIn/Glassdoor para funcionários
3. Implementar cache de dados da ReceitaWS
4. Adicionar mais fontes de dados governamentais
5. Melhorar estimativas baseadas em CNAE

## Estatísticas da Última Execução

- Empresas coletadas: 359
- Relacionamentos empresa-NCM: 34
- Sugestões geradas: 20
- Valor total importado: R$ 2.462.372.100,00
- Valor total exportado: R$ 1.163.977.860,00
- Peso participação médio: 12.96


