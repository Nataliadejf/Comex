# Como Usar os Scripts de Coleta

## 📋 Scripts Disponíveis

### 1. `executar_coleta.py` - Executar Coleta de Dados
Executa o endpoint de coleta e mostra estatísticas em tempo real.

### 2. `avaliar_metodo.py` - Avaliar Método Usado
Analisa qual método foi usado na coleta e fornece recomendações.

## 🚀 Uso Rápido (Windows)

### Executar Coleta
```batch
EXECUTAR_COLETA.bat
```

### Avaliar Método
```batch
AVALIAR_METODO.bat
```

## 🐍 Uso via Python

### 1. Executar Coleta

**Básico (24 meses, todos os NCMs):**
```bash
python backend/scripts/executar_coleta.py
```

**Com opções:**
```bash
# Coletar apenas 12 meses
python backend/scripts/executar_coleta.py --meses 12

# Coletar NCMs específicos
python backend/scripts/executar_coleta.py --ncms 86079900 73182200

# Coletar apenas importações
python backend/scripts/executar_coleta.py --tipo Importação

# Usar backend local
python backend/scripts/executar_coleta.py --local

# Backend customizado
python backend/scripts/executar_coleta.py --url https://seu-backend.onrender.com
```

**Exemplos completos:**
```bash
# Coletar últimos 6 meses de importações para NCM específico
python backend/scripts/executar_coleta.py --meses 6 --tipo Importação --ncms 86079900

# Coletar todos os dados (24 meses, todos os NCMs, ambos os tipos)
python backend/scripts/executar_coleta.py --meses 24
```

### 2. Avaliar Método Usado

**Básico:**
```bash
python backend/scripts/avaliar_metodo.py
```

**Com opções:**
```bash
# Usar backend local
python backend/scripts/avaliar_metodo.py --local

# Analisar arquivo específico
python backend/scripts/avaliar_metodo.py --arquivo comex_data/logs/coleta_20250105_120000.json

# Backend customizado
python backend/scripts/avaliar_metodo.py --url https://seu-backend.onrender.com
```

## 📊 O que os Scripts Fazem

### `executar_coleta.py`

1. **Envia requisição** para `/coletar-dados-ncms`
2. **Mostra progresso** em tempo real
3. **Exibe estatísticas:**
   - Total de registros coletados
   - Método usado (API, CSV Scraper, etc.)
   - Meses processados
   - Erros encontrados
4. **Salva resultado** em `comex_data/logs/coleta_YYYYMMDD_HHMMSS.json`

### `avaliar_metodo.py`

1. **Busca última coleta** (arquivo JSON ou endpoint)
2. **Analisa método usado:**
   - Detecta se foi API, CSV Scraper ou Scraper tradicional
   - Avalia sucesso/falha
   - Identifica problemas
3. **Verifica banco de dados:**
   - Total de registros
   - Valores e volumes
   - Meses com dados
4. **Fornece recomendações** baseadas nos resultados
5. **Salva relatório** em `comex_data/logs/avaliacao_YYYYMMDD_HHMMSS.json`

## 📝 Exemplo de Saída

### Executar Coleta
```
============================================================
EXECUTANDO COLETA DE DADOS
============================================================
URL: https://comex-backend-wjco.onrender.com/coletar-dados-ncms
Meses: 24
NCMs: Todos (geral)
Tipo Operação: Ambos
------------------------------------------------------------
Enviando requisição...

✅ COLETA INICIADA COM SUCESSO!
------------------------------------------------------------
Mensagem: Coleta concluída: 15234 registros usando CSV Scraper

📊 ESTATÍSTICAS:
  Total de registros: 15234
  Método usado: CSV Scraper
  Usou API: False
  Meses processados: 24
  Primeiros meses: 2024-01, 2024-02, 2024-03, 2024-04, 2024-05
  ... e mais 19 meses

✅ Nenhum erro encontrado!
```

### Avaliar Método
```
============================================================
RELATÓRIO DE AVALIAÇÃO - MÉTODO DE COLETA
============================================================

📡 MÉTODO USADO:
   CSV Scraper
   Usou API: Não

📊 ESTATÍSTICAS DA COLETA:
   Total de registros: 15,234
   Meses processados: 24
   Erros encontrados: 0

✅ STATUS: SUCESSO TOTAL

💾 BANCO DE DADOS:
   Valor total: US$ 1,234,567.89
   Volume importações: 1,234,567.89 KG
   Volume exportações: 987,654.32 KG
   Meses com dados: 24

💡 RECOMENDAÇÕES:
   ✅ CSV Scraper funcionando - usando bases de dados brutas
   💡 Este método é mais confiável para dados históricos
   ✅ 15,234 registros coletados com sucesso!
```

## 🔧 Opções Avançadas

### Parâmetros do `executar_coleta.py`

- `--url`: URL do backend (padrão: Render)
- `--meses`: Número de meses (padrão: 24)
- `--ncms`: Lista de NCMs específicos
- `--tipo`: Tipo de operação (Importação/Exportação)
- `--local`: Usar backend local

### Parâmetros do `avaliar_metodo.py`

- `--url`: URL do backend (padrão: Render)
- `--local`: Usar backend local
- `--arquivo`: Caminho para arquivo JSON específico

## 📁 Arquivos Gerados

Os scripts salvam arquivos em `comex_data/logs/`:

- `coleta_YYYYMMDD_HHMMSS.json` - Resultado da coleta
- `avaliacao_YYYYMMDD_HHMMSS.json` - Relatório de avaliação

## 🐛 Troubleshooting

### Erro: "Python não encontrado"
- Instale Python 3.8+ e adicione ao PATH

### Erro: "Timeout"
- Coletas grandes podem demorar vários minutos
- Verifique os logs do Render para progresso

### Erro: "Connection refused"
- Verifique se o backend está rodando
- Use `--local` para backend local
- Verifique a URL com `--url`

### Nenhum registro coletado
- Execute `avaliar_metodo.py` para diagnóstico
- Verifique logs do backend
- Tente coletar menos meses primeiro

## 💡 Dicas

1. **Comece pequeno:** Teste com `--meses 3` primeiro
2. **Monitore logs:** Acompanhe os logs do Render durante a coleta
3. **Use avaliação:** Sempre execute `avaliar_metodo.py` após coletar
4. **Arquivos JSON:** Os arquivos JSON salvos podem ser analisados depois

## 🔗 Links Úteis

- Backend Render: https://comex-backend-wjco.onrender.com/docs
- Swagger UI: https://comex-backend-wjco.onrender.com/docs
- Logs Render: Dashboard → comex-backend → Logs

---

**Última atualização**: 05/01/2026



