# Sistema de Análise de Sinergias e CNAE

## 📋 Visão Geral

Este sistema integra dados de importação/exportação com:
1. **Lista de Empresas do MDIC** (CNPJ, nome, UF)
2. **Arquivo CNAE** (`NOVO CNAE.xlsx`) - Classificação das empresas
3. **Dados de Operações** (Comex Stat)

Para identificar **sinergias** e gerar **sugestões** de importação/exportação por empresa.

## 🎯 Funcionalidades

### 1. Análise de Sinergias por Estado
- Mapeia importações e exportações por UF
- Calcula índice de sinergia
- Identifica estados com maior potencial

### 2. Análise de Sinergias por Empresa
- Cruza empresas do MDIC com operações
- Integra com CNAE para classificação
- Gera sugestões personalizadas

### 3. Sugestões por Empresa
- Analisa padrões de importação/exportação
- Considera CNAE e classificação
- Sugere oportunidades de negócio

## 🚀 Como Usar

### 1. Carregar Arquivo CNAE

**Via Endpoint:**
```bash
POST /carregar-cnae?arquivo_path=C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx
```

**Via Swagger:**
1. Acesse: `https://comex-backend-wjco.onrender.com/docs`
2. Procure por `POST /carregar-cnae`
3. Execute (usa caminho padrão automaticamente)

### 2. Analisar Sinergias por Estado

**Via Endpoint:**
```bash
GET /analisar-sinergias-estado?uf=SP
```

**Resultado:**
```json
{
  "uf_filtrada": "SP",
  "total_estados": 27,
  "estados_com_sinergia": 15,
  "sinergias": [
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
      "sugestao": "Estado com alta sinergia - empresas podem diversificar operações"
    }
  ]
}
```

### 3. Analisar Sinergias por Empresa

**Via Endpoint:**
```bash
POST /analisar-sinergias-empresas?limite=100&ano=2024
```

**Resultado:**
```json
{
  "success": true,
  "total_empresas_mdic": 5000,
  "empresas_analisadas": 100,
  "cnae_carregado": true,
  "resultados": [
    {
      "cnpj": "12345678000190",
      "razao_social": "EMPRESA EXEMPLO LTDA",
      "uf": "SP",
      "importacoes": {
        "total_operacoes": 50,
        "valor_total": 1000000.00
      },
      "exportacoes": {
        "total_operacoes": 0,
        "valor_total": 0.0
      },
      "potencial_sinergia": 0.5,
      "cnae": "2511000",
      "classificacao_cnae": "Fabricação de estruturas metálicas",
      "sugestao": "Empresa importadora - considere exportar produtos relacionados ao CNAE 2511000 (Fabricação de estruturas metálicas)"
    }
  ]
}
```

### 4. Sugestões para Empresa Específica

**Via Endpoint:**
```bash
GET /sugestoes-empresa/12345678000190
```

## 📊 Estrutura do Arquivo CNAE

O sistema lê automaticamente o arquivo `NOVO CNAE.xlsx` e identifica:
- **Colunas CNAE**: Código CNAE da empresa
- **Colunas CNPJ**: CNPJ da empresa
- **Colunas Empresa**: Nome/Razão Social
- **Colunas Classificação**: Categoria/Setor/Tipo

### Exemplo de Estrutura Esperada:

| CNPJ | Razão Social | CNAE | Classificação |
|------|--------------|------|---------------|
| 12345678000190 | EMPRESA EXEMPLO LTDA | 2511000 | Fabricação de estruturas metálicas |
| 98765432000110 | OUTRA EMPRESA SA | 2829001 | Fabricação de máquinas |

## 🔍 Como Funciona

### 1. Mapeamento de Estados
- Agrupa operações por UF
- Calcula volumes de importação e exportação
- Identifica estados que fazem ambos (sinergia)

### 2. Mapeamento de Empresas
- Busca empresas do MDIC por CNPJ
- Cruza com operações do banco de dados
- Integra com CNAE para classificação

### 3. Cálculo de Sinergia
- **Alta (0.7-1.0)**: Empresa/Estado já faz ambos
- **Média (0.3-0.7)**: Potencial para diversificar
- **Baixa (<0.3)**: Foco em uma operação

### 4. Geração de Sugestões
- Baseada em padrões de CNAE
- Considera histórico de operações
- Sugere oportunidades relacionadas

## 💡 Exemplos de Sugestões

### Empresa Importadora
```
"Empresa importadora - considere exportar produtos relacionados 
ao CNAE 2511000 (Fabricação de estruturas metálicas)"
```

### Empresa Exportadora
```
"Empresa exportadora - considere importar insumos relacionados 
ao CNAE 2829001 (Fabricação de máquinas)"
```

### Estado com Sinergia
```
"Estado com alta sinergia - empresas podem diversificar operações"
```

## ⚙️ Configuração

### Arquivo CNAE
Por padrão, o sistema procura em:
```
C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx
```

Você pode especificar outro caminho:
```bash
POST /carregar-cnae?arquivo_path=/caminho/para/arquivo.xlsx
```

### Dependências
O sistema requer:
- `pandas` - Para ler Excel
- `openpyxl` - Para processar arquivos .xlsx

## 📝 Fluxo Completo de Uso

1. **Carregar CNAE:**
   ```bash
   POST /carregar-cnae
   ```

2. **Coletar Empresas do MDIC:**
   ```bash
   POST /coletar-empresas-mdic?ano=2024
   ```

3. **Analisar Sinergias por Estado:**
   ```bash
   GET /analisar-sinergias-estado
   ```

4. **Analisar Sinergias por Empresa:**
   ```bash
   POST /analisar-sinergias-empresas?limite=100
   ```

5. **Obter Sugestões para Empresa:**
   ```bash
   GET /sugestoes-empresa/{cnpj}
   ```

## 🎯 Casos de Uso

### 1. Identificar Oportunidades por Estado
- Ver quais estados têm maior sinergia
- Focar esforços comerciais nesses estados
- Identificar estados com potencial não explorado

### 2. Prospecção de Clientes
- Encontrar empresas que só importam (potencial para exportar)
- Encontrar empresas que só exportam (potencial para importar)
- Identificar empresas por CNAE/classificação

### 3. Análise de Mercado
- Entender padrões por setor (CNAE)
- Identificar sinergias entre setores
- Mapear cadeias produtivas

## ⚠️ Limitações

1. **Dados Anonimizados**: Nem todas as operações têm CNPJ
2. **Lista MDIC Anual**: Pode ter atraso de alguns meses
3. **CNAE Opcional**: Empresas podem não estar no arquivo
4. **Sugestões Genéricas**: Baseadas em padrões, não garantem sucesso

## 🔗 Endpoints Disponíveis

- `POST /carregar-cnae` - Carrega arquivo CNAE
- `GET /analisar-sinergias-estado` - Análise por estado
- `POST /analisar-sinergias-empresas` - Análise por empresa
- `GET /sugestoes-empresa/{cnpj}` - Sugestões específicas
- `POST /coletar-empresas-mdic` - Coleta empresas do MDIC
- `POST /cruzar-dados-empresas` - Cruza operações com empresas

---

**Última atualização**: 06/01/2026

