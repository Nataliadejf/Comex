# 📊 Análise de Empresas Recomendadas

Este documento explica como funciona a análise e consolidação de empresas recomendadas.

## 🎯 Objetivo

Criar uma tabela consolidada (`empresas_recomendadas`) que relaciona dados de múltiplas fontes e identifica prováveis importadores e exportadores.

## 📋 Processo

### 1. Verificar Dados no Banco

Primeiro, verifique se há dados nas tabelas:

```bash
python backend/scripts/verificar_dados.py
```

Este script verifica:
- `operacoes_comex` (tabela antiga)
- `comercio_exterior` (nova tabela)
- `empresas` (nova tabela)
- `empresas_recomendadas` (tabela consolidada)

### 2. Executar Análise

Execute o script de análise:

```bash
# Localmente
python backend/scripts/analisar_empresas_recomendadas.py

# No Render Shell
cd /opt/render/project/src/backend
python scripts/analisar_empresas_recomendadas.py
```

## 🔄 O que o Script Faz

1. **Analisa OperacaoComex:**
   - Busca empresas importadoras e exportadoras
   - Agrega valores, volumes e NCMs por empresa

2. **Analisa ComercioExterior + Empresa:**
   - Busca empresas da tabela `empresas`
   - Relaciona com dados de `comercio_exterior` por estado/NCM

3. **Consolida Dados:**
   - Mescla dados de todas as fontes
   - Remove duplicatas
   - Calcula métricas consolidadas

4. **Classifica Empresas:**
   - **Provável Importador:** `valor_importacao > valor_exportacao`
   - **Provável Exportador:** `valor_exportacao > valor_importacao`
   - **Ambos:** Ambos os valores significativos

5. **Calcula Peso de Participação:**
   - 50% = volume financeiro importado
   - 40% = volume financeiro exportado
   - 10% = quantidade de NCMs movimentados
   - Normalizado para 0-100

6. **Salva na Tabela:**
   - Cria/atualiza tabela `empresas_recomendadas`
   - Limpa dados antigos antes de inserir novos

## 📊 Estrutura da Tabela

```sql
CREATE TABLE empresas_recomendadas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14),
    nome VARCHAR(255) NOT NULL,
    cnae VARCHAR(10),
    estado VARCHAR(2),
    tipo_principal VARCHAR(20), -- 'importadora', 'exportadora', 'ambos'
    provavel_importador INTEGER DEFAULT 0, -- 1=sim, 0=não
    provavel_exportador INTEGER DEFAULT 0, -- 1=sim, 0=não
    valor_total_importacao_usd FLOAT DEFAULT 0,
    valor_total_exportacao_usd FLOAT DEFAULT 0,
    volume_total_importacao_kg FLOAT DEFAULT 0,
    volume_total_exportacao_kg FLOAT DEFAULT 0,
    ncms_importacao TEXT, -- NCMs separados por vírgula
    ncms_exportacao TEXT, -- NCMs separados por vírgula
    total_operacoes_importacao INTEGER DEFAULT 0,
    total_operacoes_exportacao INTEGER DEFAULT 0,
    peso_participacao FLOAT DEFAULT 0, -- Score 0-100
    data_analise TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Uso no Dashboard

O endpoint `/dashboard/stats` agora:

1. **Primeiro** tenta buscar da tabela `empresas_recomendadas` (mais eficiente)
2. **Se não encontrar**, busca de `comercio_exterior` e `empresas`
3. **Se ainda não encontrar**, busca de `operacoes_comex` (tabela antiga)
4. **Se não houver dados**, retorna resposta vazia rapidamente (não trava)

## ⚠️ Importante

- Execute a análise **após** importar dados
- A análise pode demorar alguns minutos para grandes volumes
- A tabela é **limpa** antes de cada análise (dados antigos são removidos)
- Execute periodicamente para manter dados atualizados

## 🔍 Verificar Resultados

```bash
python -c "
from database.database import SessionLocal
from database.models import EmpresasRecomendadas
from sqlalchemy import func

db = SessionLocal()
total = db.query(func.count(EmpresasRecomendadas.id)).scalar()
imp = db.query(func.count(EmpresasRecomendadas.id)).filter(
    EmpresasRecomendadas.provavel_importador == 1
).scalar()
exp = db.query(func.count(EmpresasRecomendadas.id)).filter(
    EmpresasRecomendadas.provavel_exportador == 1
).scalar()

print(f'Total: {total}')
print(f'Prováveis importadoras: {imp}')
print(f'Prováveis exportadoras: {exp}')
db.close()
"
```
