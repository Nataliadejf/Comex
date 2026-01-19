# 🔍 Como Validar o Sistema Completo

## 🎯 O que o Script Valida

O script `validar_sistema_completo.py` verifica:

1. ✅ **Conexão com BigQuery**
   - Credenciais configuradas
   - Conexão funcionando
   - Query de teste executada

2. ✅ **Banco de Dados PostgreSQL**
   - Conexão funcionando
   - Tabelas existem
   - Quantidade de registros em cada tabela
   - Detalhes de importações/exportações

3. ✅ **Arquivos CSV**
   - Diretório `comex_data/comexstat_csv` existe
   - Arquivos encontrados
   - Tamanho dos arquivos

4. ✅ **Relacionamentos**
   - Tabela `empresas_recomendadas` populada
   - Relacionamento entre `operacoes_comex` e `empresas`
   - CNPJs relacionados

## 🚀 Como Executar

### **MÉTODO 1: Via API HTTP (Recomendado - Sem Shell)** ⭐

**Não precisa de Shell!** Funciona no plano free do Render.

1. **Acesse**: `https://seu-backend.onrender.com/validar-sistema`
   - Substitua `seu-backend` pela URL real do seu backend
   - Exemplo: `https://comex-backend-gecp.onrender.com/validar-sistema`

2. **Ou use Swagger**:
   - Acesse: `https://seu-backend.onrender.com/docs`
   - Procure: `GET /validar-sistema`
   - Clique em "Try it out" → "Execute"

**Veja guia completo:** `VALIDAR_SISTEMA_VIA_API.md`

---

### **MÉTODO 2: Via Shell (Requer Plano Pago)**

1. **Render Dashboard** → `comex-backend` → **"Shell"**

2. **Execute:**
   ```bash
   cd backend
   python scripts/validar_sistema_completo.py
   ```

---

### **MÉTODO 3: Localmente**

```bash
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
cd backend
python scripts/validar_sistema_completo.py
```

## 📊 Exemplo de Saída

```
================================================================================
🔍 VALIDAÇÃO COMPLETA DO SISTEMA COMEX ANALYZER
================================================================================
Data/Hora: 2026-01-11 21:00:00

================================================================================
🔍 VALIDAÇÃO 1: BigQuery
================================================================================
✅ Credenciais do Google Cloud encontradas
✅ Conectado ao BigQuery com sucesso
✅ Query de teste executada com sucesso

================================================================================
🔍 VALIDAÇÃO 2: Banco de Dados PostgreSQL
================================================================================
✅ Conexão com PostgreSQL OK
✅ operacoes_comex: 1,234,567 registros
  📊 Importações: 600,000
  📊 Exportações: 634,567
  📊 CNPJs Importadores únicos: 50,000
  📊 CNPJs Exportadores únicos: 45,000
✅ empresas: 10,000 registros
⚠️ empresas_recomendadas: VAZIA (0 registros)

================================================================================
🔍 VALIDAÇÃO 3: Arquivos CSV
================================================================================
✅ Diretório encontrado: comex_data/comexstat_csv
  📄 conjunto-dados.csv (1,234,567 bytes)
  📄 H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx (5,678,901 bytes)

✅ Diretório csv_downloads encontrado: 50 arquivos
  📊 Importações: 25 arquivos
  📊 Exportações: 25 arquivos

================================================================================
🔍 VALIDAÇÃO 4: Relacionamentos e Recomendações
================================================================================
⚠️ Tabela empresas_recomendadas está VAZIA
💡 Execute o script de análise de sinergias para popular

📊 Relacionamento Operações ↔ Empresas:
  CNPJs em operacoes_comex: 50,000
  CNPJs em empresas: 10,000
  CNPJs relacionados: 5,000
  Percentual relacionado: 10.0%

================================================================================
📋 RESUMO DA VALIDAÇÃO
================================================================================
✅ Status Geral: ATENÇÃO

⚠️ Problemas Encontrados:
  - Tabela empresas_recomendadas está vazia
  - Nenhum relacionamento entre operacoes_comex e empresas

💡 Recomendações:
  - Execute script de análise de sinergias
  - Execute script de análise de sinergias para criar relacionamentos
```

## 🔧 Problemas Comuns e Soluções

### Problema: BigQuery não conectado

**Sintomas:**
```
❌ Credenciais do Google Cloud NÃO encontradas
```

**Solução:**
1. Render Dashboard → `comex-backend` → Environment
2. Adicione: `GOOGLE_APPLICATION_CREDENTIALS_JSON` com o JSON das credenciais
3. Faça deploy novamente

### Problema: Tabela operacoes_comex vazia

**Sintomas:**
```
⚠️ operacoes_comex: VAZIA (0 registros)
```

**Solução:**
1. Execute coleta de dados do Comex Stat
2. Via API: `POST /coletar-dados`
3. Ou via script: `python scripts/coletar_dados_comexstat.py`

### Problema: Tabela empresas_recomendadas vazia

**Sintomas:**
```
⚠️ Tabela empresas_recomendadas está VAZIA
```

**Solução:**
1. Execute script de análise de sinergias:
   ```bash
   python scripts/analisar_empresas_recomendadas.py
   ```
2. Ou via API: `POST /dashboard/analisar-sinergias`

### Problema: Nenhum relacionamento encontrado

**Sintomas:**
```
⚠️ NENHUM relacionamento encontrado entre operacoes_comex e empresas
```

**Solução:**
1. Certifique-se que ambas as tabelas têm dados
2. Execute script de análise de sinergias
3. Verifique se os CNPJs estão no formato correto (apenas números)

## 📝 Checklist de Validação

Após executar o script, verifique:

- [ ] BigQuery conectado
- [ ] Tabela `operacoes_comex` tem dados
- [ ] Tabela `empresas` tem dados
- [ ] Tabela `empresas_recomendadas` tem dados
- [ ] Relacionamentos entre tabelas funcionando
- [ ] Arquivos CSV encontrados

## 🎯 Próximos Passos

Se o script identificar problemas:

1. **Siga as recomendações** mostradas no resumo
2. **Execute os scripts sugeridos**
3. **Execute a validação novamente** para confirmar correção

## 💡 Dica

Execute este script **regularmente** para garantir que o sistema está funcionando corretamente, especialmente após:
- Deploy no Render
- Coleta de novos dados
- Atualizações no código
