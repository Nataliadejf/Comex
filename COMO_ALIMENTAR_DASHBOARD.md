# Como Alimentar o Dashboard com Dados das Planilhas

## 📋 Visão Geral

O dashboard agora está configurado para exibir:
- ✅ **Empresas Recomendadas** nas seções "Prováveis Importadores" e "Prováveis Exportadores"
- ✅ **Dados do Excel ComexStat** (importações e exportações)
- ✅ **Estatísticas** baseadas nos dados processados

## 🚀 Passo a Passo

### 1. Processar Dados do Excel

Execute o script para processar o arquivo Excel e gerar os JSONs:

```bash
python backend/scripts/carregar_dados_excel_dashboard.py
```

**Ou use o script batch:**
```bash
ALIMENTAR_DASHBOARD.bat
```

Este script cria:
- `backend/data/resumo_dados_comexstat.json` - Resumo geral
- `backend/data/dados_ncm_comexstat.json` - Dados por NCM

### 2. Gerar Empresas Recomendadas

Execute o script para gerar a tabela de empresas recomendadas:

```bash
python backend/scripts/gerar_empresas_recomendadas.py
```

Este script cria:
- `backend/data/empresas_recomendadas.xlsx` - Tabela completa
- `backend/data/empresas_recomendadas.csv` - Versão CSV

### 3. Reiniciar o Backend

Após processar os dados, reinicie o backend para carregar os novos arquivos:

```bash
# Parar backend atual (Ctrl+C)
# Iniciar novamente
INICIAR_BACKEND.bat
```

### 4. Acessar o Dashboard

1. Acesse o frontend: `http://localhost:3000`
2. Faça login
3. O dashboard deve exibir:
   - **Cards de estatísticas** com valores do Excel
   - **Prováveis Importadores** com empresas recomendadas que importam
   - **Prováveis Exportadores** com empresas recomendadas que exportam
   - **Gráficos** com dados mensais
   - **Tabela de empresas recomendadas** completa

## 📊 Como Funciona

### Empresas nas Seções Corretas

O sistema identifica automaticamente:
- **Prováveis Importadores**: Empresas com `Importado (R$)` > 0
- **Prováveis Exportadores**: Empresas com `Exportado (R$)` > 0

### Dados do Dashboard

O endpoint `/dashboard/stats` agora:
1. Busca dados do banco de dados primeiro
2. Se não houver dados, usa os arquivos JSON do Excel
3. Inclui empresas recomendadas nas seções corretas

### Endpoints Disponíveis

- `GET /dashboard/stats` - Estatísticas gerais (agora inclui dados do Excel)
- `GET /dashboard/empresas-recomendadas` - Lista completa de empresas
- `GET /dashboard/empresas-importadoras` - Empresas importadoras (para "Prováveis Importadores")
- `GET /dashboard/empresas-exportadoras` - Empresas exportadoras (para "Prováveis Exportadores")
- `GET /dashboard/dados-comexstat` - Resumo dos dados do Excel
- `GET /dashboard/dados-ncm-comexstat` - Dados agregados por NCM

## 🔧 Estrutura dos Dados

### Empresas Recomendadas

Cada empresa tem:
- CNPJ
- Razão Social / Nome Fantasia
- Estado (UF)
- NCM Relacionado
- Importado (R$) - Valor em Reais
- Exportado (R$) - Valor em Reais
- Peso Participação (0-100) - Score calculado
- Sugestão - CLIENTE_POTENCIAL ou FORNECEDOR_POTENCIAL

### Dados ComexStat

O resumo inclui:
- Total de registros de importação/exportação
- Valores totais em USD e BRL
- Dados por estado
- Top NCMs movimentados

## ✅ Verificação

Para verificar se está funcionando:

1. **Verifique os arquivos gerados:**
   ```bash
   dir backend\data\*.json
   dir backend\data\*.xlsx
   ```

2. **Teste os endpoints:**
   - Acesse: `http://localhost:8000/dashboard/dados-comexstat`
   - Deve retornar JSON com os dados

3. **Verifique o dashboard:**
   - Cards devem mostrar valores > 0
   - Seções "Prováveis Importadores/Exportadores" devem mostrar empresas
   - Gráficos devem ter dados

## 🐛 Troubleshooting

### Problema: Dashboard não mostra dados

**Solução:**
1. Verifique se os arquivos JSON foram criados em `backend/data/`
2. Reinicie o backend após gerar os arquivos
3. Verifique o console do navegador (F12) para erros
4. Verifique os logs do backend

### Problema: Empresas não aparecem nas seções corretas

**Solução:**
1. Verifique se `empresas_recomendadas.xlsx` existe
2. Verifique se as empresas têm valores de importação/exportação
3. Execute `gerar_empresas_recomendadas.py` novamente

### Problema: Valores estão zerados

**Solução:**
1. Verifique se o arquivo Excel foi processado corretamente
2. Execute `carregar_dados_excel_dashboard.py` novamente
3. Verifique se o arquivo Excel está no caminho correto

## 📝 Notas Importantes

1. **Dados do Excel**: Os dados são processados e salvos em JSON para acesso rápido
2. **Empresas Recomendadas**: Baseadas nos dados agregados do Excel (UF + NCM)
3. **Fallback**: Se não houver dados no banco, o sistema usa os JSONs do Excel
4. **Performance**: Os JSONs são carregados uma vez e reutilizados

## 🎯 Próximos Passos

Para melhorar ainda mais:
1. Carregar dados do Excel no banco de dados (script `carregar_excel_para_banco.py`)
2. Buscar empresas reais via APIs públicas
3. Enriquecer com mais dados (CNAE, endereços completos, etc.)


