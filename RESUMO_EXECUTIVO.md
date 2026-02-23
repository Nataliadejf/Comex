# 📋 RESUMO EXECUTIVO: Análise de Dashboard - Cards com Valores Iguais/Vazios

## 🎯 PROBLEMA IDENTIFICADO

Usuário relata: **"Cards do dashboard mostram mesmos valores para empresas diferentes (VALE, HIDRAU) e filtros não funcionam"**

## ✅ ANÁLISE COMPLETA REALIZADA

Executei investigação em 3 camadas:

### 1️⃣ **Frontend / Backend** (LAV anterior - já foi CORRIGIDO)
- ✅ Parâmetros de filtro não eram enviados ao API → **CORRIGIDO**
- ✅ Backend aplicava filtros globais invalidando por empresa → **CORRIGIDO**
- ✅ Commit: `fix: Corrigir filtro de empresa no dashboard`

### 2️⃣ **Camada de Dados: Qualidade** (ENCONTRADO PROBLEMA CRÍTICO)
- 📊 **643.701 registros** no banco
- 🔴 **79% (510.000) são "lixo":** `arquivo_origem='BigQuery'` + `valor_fob=0.0` + `ncm='00000000'`
- 🟢 **21% (133.701) são bons:** 2 fontes com dados válidos (Excel 2025 + outro com $254 Mi)

### 3️⃣ **Situação VALE e HIDRAU**
- **VALE S.A.**: 3.242 registros encontrados
  - ❌ **TODOS com valor_fob=0.0**
  - ❌ Arquivo: BigQuery (dados históricos 1999-2010, não validados)
  - ❌ NCM: 00000000 (código inválido)
  - ✅ Presença por UF confirmada: MA, RO, PB, BA, ES, MG

- **HIDRAU**: 1.087 registros encontrados
  - ❌ **TODOS com valor_fob=0.0**
  - ❌ Arquivo: BigQuery (mesma situação)
  - ❌ NCM: 00000000
  - ✅ Presença por UF confirmada: MG, PR, RS
  - ⚠️ Nome não é exato (match por LIKE '%HIDRAU%')

- **Excel 2025:** ❌ Não contém VALE nem HIDRAU → não há dados recentes para essas empresas

## 🔍 POR QUE OS CARDS MOSTRAM "0"

```
SELECT SUM(valor_fob) FROM operacoes_comex 
WHERE razao_social_importador LIKE '%VALE%'
→ Resultado: 0.0 (porque todos os 3.242 registros têm valor_fob=0.0)
```

Dashboard filtra, encontra registros, mas SUM=0 → card exibe "0" ou fica vazio.

## 📁 ARQUIVOS GERADOS

Todos salvos em `backend/`:

| Script | Função |
|--------|--------|
| `check_cnpj_operations.py` | Lista CNPJs por UF e NCM |
| `sample_raw_rows.py` | Amostra 5 linhas brutas por CNPJ |
| `diagnose_data_quality.py` | Distribuição de valor_fob e arquivo_origem |
| `check_excel_companies.py` | Verifica presença em Excel 2025 |
| `clean_low_quality_data.py` | Simula/documenta limpeza de 510k registros |
| `DIAGNOSTICO_COMPLETO.md` | Relatório detalhado com soluções |

## 🚀 PRÓXIMOS PASSOS RECOMENDADOS

### **OPÇÃO A: Limpar dados (Recomendado)**
```bash
python backend/clean_low_quality_data.py  # Ver o que será deletado
# Depois descomente DELETE no script para executar
```
**Efeito:** Dashboard fica "limpo" mas VALE/HIDRAU desaparecem (só tinham dados zerados)
**Resultado:** 133.701 registros válidos restam

### **OPÇÃO B: Importar VALE/HIDRAU manualmente**
- Buscar dados de importação/exportação reais para VALE e HIDRAU
- Importar via Excel com novo script
- Usar CNPJ para relacionar com `empresas` (robusto)

### **OPÇÃO C: Implementar foreign key CNPJ**
- Relacionar `operacoes_comex.cnpj_importador` com `empresas.cnpj`
- Eliminar dependência de match por `razao_social` (string sujeita a variações)
- Mais robusto para filtros por empresa no dashboard

### **OPÇÃO D: Tudo acima (ideal)**
1. Limpar registros BigQuery zerados
2. Importar dados reais de VALE/HIDRAU
3. Implementar FK CNPJ
4. Testar dashboard com ambas as empresas

---

## 💡 RECOMENDAÇÃO IMEDIATA

**Sugiro:** **Fazer backup → Opção A+B+C em paralelo**

1. **Hoje:** `python backend/clean_low_quality_data.py` → DELETE (remove 510k lixo)
2. **Hoje:** Importar VALE/HIDRAU com dados reais (você tem os dados no arquivo?)
3. **Próxima sprint:** FK CNPJ + dashboard aprimora filtros

**Custo de não fazer:** Dashboard continua mostrando "0" para essas empresas indefinidamente.

---

## 📞 DÚVIDAS?

Qual opção você prefere? Tenho scripts prontos para:
- [ ] Executar LIMPEZA (remover 510k registros BigQuery)
- [ ] IMPORTAR VALE/HIDRAU (se vier arquivo com dados)
- [ ] IMPLEMENTAR FK CNPJ (migration + query update)
- [ ] Tudo junto (mais tempo mas definitivo)

Avise!
