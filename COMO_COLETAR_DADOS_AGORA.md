# 🚀 Como Coletar Dados Agora - Guia Rápido

## ❌ Problema Atual

O endpoint `/coletar-dados` retornou `total_registros: 0`, ou seja, **não coletou nenhum dado**.

## ✅ Soluções Disponíveis

### **SOLUÇÃO 1: Usar Coleta Enriquecida** ⭐ RECOMENDADO

Este é o método mais confiável! Baixa dados **diretamente do portal oficial do MDIC**.

#### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /coletar-dados-enriquecidos`
3. **Parâmetros**:
   - `meses`: `12` (ou `24` para mais dados)
4. **Clique em**: "Try it out" → "Execute"
5. **Aguarde** alguns minutos (pode demorar 5-10 minutos)

#### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/coletar-dados-enriquecidos?meses=12' \
  -H 'accept: application/json'
```

**Por que usar este endpoint:**
- ✅ Baixa dados diretamente do MDIC (mais confiável)
- ✅ Não depende de APIs externas
- ✅ Enriquece dados automaticamente
- ✅ Funciona no Render sem problemas

---

### **SOLUÇÃO 2: Tentar Coletar Dados Novamente**

Após o deploy do código melhorado, tente novamente:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /coletar-dados`
3. **Clique em**: "Try it out" → "Execute"
4. **Aguarde** alguns minutos

**O código melhorado agora:**
- Tenta CSV scraper diretamente se a coleta inicial falhar
- Força download dos arquivos CSV do MDIC
- Processa e importa automaticamente

---

## 📊 Após Coletar Dados

### 1. Validar se coletou dados:

```bash
GET /validar-sistema
```

Verifique se `banco_dados.total_registros.operacoes_comex` > 0

### 2. Gerar empresas recomendadas:

```bash
POST /dashboard/analisar-sinergias
```

Isso vai:
- Popular `empresas_recomendadas`
- Criar relacionamentos entre tabelas
- Gerar recomendações

### 3. Validar novamente:

```bash
GET /validar-sistema
```

Confirme que:
- `operacoes_comex` tem dados
- `empresas_recomendadas` tem dados
- Relacionamentos funcionando

### 4. Testar o dashboard:

Acesse o frontend e veja se os dados aparecem!

---

## 🎯 Ordem Recomendada de Execução

1. ✅ **Coletar dados** → `POST /coletar-dados-enriquecidos?meses=12`
2. ✅ **Aguardar** alguns minutos
3. ✅ **Validar** → `GET /validar-sistema`
4. ✅ **Gerar recomendações** → `POST /dashboard/analisar-sinergias`
5. ✅ **Validar novamente** → `GET /validar-sistema`
6. ✅ **Testar dashboard** → Acesse o frontend

---

## ⏱️ Tempo Estimado

- **Coleta de dados**: 5-10 minutos (depende da quantidade de meses)
- **Análise de sinergias**: 2-5 minutos
- **Total**: ~10-15 minutos

---

## 🐛 Se Ainda Não Funcionar

### Problema: Coleta enriquecida também retorna 0 registros

**Possíveis causas:**
- Portal do MDIC pode estar temporariamente indisponível
- URLs dos arquivos CSV podem ter mudado
- Limitações de rede no Render

**Solução alternativa:**
- Aguarde algumas horas e tente novamente
- Ou use os arquivos CSV locais (precisa criar endpoint de upload)

### Problema: Timeout durante coleta

**Solução:**
- Reduza o número de meses (use `meses=6` ao invés de `24`)
- Execute múltiplas vezes com períodos menores

---

## 💡 Dica Final

**Recomendação:** Use `POST /coletar-dados-enriquecidos` primeiro!

Este endpoint é mais confiável e completo. Se funcionar, você terá:
- ✅ Dados de operações
- ✅ Dados enriquecidos com empresas
- ✅ Dados prontos para análise

**Depois disso**, execute `POST /dashboard/analisar-sinergias` para gerar as recomendações!
