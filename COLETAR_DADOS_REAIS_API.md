# Coletar Dados Reais da API Comex Stat

## 🎯 Objetivo

Coletar dados reais de todos os NCMs da API oficial do Comex Stat.

## ⚠️ IMPORTANTE: Configuração da API

Para coletar dados reais, você precisa configurar a URL da API Comex Stat no Render:

### Passo 1: Configurar Variáveis de Ambiente no Render

1. **Acesse o Render Dashboard:**
   - Vá em `comex-backend` → "Environment"

2. **Adicione/Verifique as variáveis:**
   - `COMEX_STAT_API_URL`: URL da API oficial do Comex Stat
     - Exemplo: `https://comexstat.mdic.gov.br/api` ou `http://comexstat.mdic.gov.br`
   - `COMEX_STAT_API_KEY`: Chave da API (se necessário, pode deixar vazio se a API for pública)

3. **Salve as alterações**

### Passo 2: Verificar URL da API

A URL da API pode ser:
- `https://comexstat.mdic.gov.br/api`
- `http://comexstat.mdic.gov.br`
- Ou outra URL fornecida pelo MDIC

**Verifique a documentação oficial do Comex Stat para a URL correta.**

## 📋 Como Coletar Dados Reais

### Método 1: Via Endpoint `/coletar-dados-ncms` (Recomendado)

**Coletar todos os NCMs (dados gerais):**

```javascript
fetch('https://comex-backend-wjco.onrender.com/coletar-dados-ncms', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ncms: null,  // null = todos os NCMs
    meses: 24,   // últimos 24 meses
    tipo_operacao: null  // null = ambos (Importação e Exportação)
  })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Coleta iniciada:', data);
  console.log('Total de registros:', data.stats.total_registros);
  console.log('Meses processados:', data.stats.meses_processados);
  console.log('Erros:', data.stats.erros);
});
```

**Via Swagger:**
1. Acesse: `https://comex-backend-wjco.onrender.com/docs`
2. Procure por `POST /coletar-dados-ncms`
3. Body:
   ```json
   {
     "ncms": null,
     "meses": 24,
     "tipo_operacao": null
   }
   ```
4. Execute

### Método 2: Via Endpoint `/coletar-dados` (Original)

```javascript
fetch('https://comex-backend-wjco.onrender.com/coletar-dados', {
  method: 'POST'
})
.then(r => r.json())
.then(data => {
  console.log('✅ Coleta concluída:', data);
});
```

## 🔍 Verificar se a API Está Configurada

### Teste 1: Verificar Variáveis de Ambiente

No Render Dashboard → `comex-backend` → "Environment":
- Verifique se `COMEX_STAT_API_URL` está definida
- Verifique se `COMEX_STAT_API_KEY` está definida (pode estar vazia)

### Teste 2: Verificar Logs do Backend

No Render Dashboard → `comex-backend` → "Logs":
- Procure por: `API do Comex Stat não configurada`
- Ou: `API do Comex Stat acessível`

### Teste 3: Testar Coleta

Execute a coleta e verifique os logs:
- Se aparecer `API do Comex Stat não está disponível` → API não configurada
- Se aparecer `Coletando dados gerais (todos os NCMs)...` → API configurada e funcionando

## ⏰ Tempo Estimado

- **Coleta completa (todos NCMs, 24 meses)**: 30-60 minutos
- **Coleta parcial (alguns meses)**: 5-15 minutos
- **A coleta roda em background** - você pode acompanhar pelos logs

## 📊 Monitorar Coleta

### Ver Logs em Tempo Real:

1. No Render Dashboard → `comex-backend` → "Logs"
2. Procure por:
   - `Coletando dados gerais (todos os NCMs)...`
   - `Coletando 2024-01 - Importação...`
   - `✓ X registros salvos para 2024-01 - Importação`
   - `Erro ao coletar` (se houver erros)

### Verificar Resultados:

Após a coleta, teste o banco:
```javascript
fetch('https://comex-backend-wjco.onrender.com/test/empresas')
  .then(r => r.json())
  .then(data => {
    console.log('Total de registros:', data.total_registros);
    console.log('Valor total:', data.valor_total_importacoes + data.valor_total_exportacoes);
  });
```

## ⚠️ Problemas Comuns

### Problema 1: "API do Comex Stat não está disponível"

**Causa**: `COMEX_STAT_API_URL` não está configurada no Render

**Solução**:
1. No Render Dashboard → `comex-backend` → "Environment"
2. Adicione `COMEX_STAT_API_URL` com a URL correta da API
3. Reinicie o serviço

### Problema 2: "Erro ao coletar dados"

**Causa**: API retornando erro ou URL incorreta

**Solução**:
1. Verifique a URL da API no Render
2. Verifique os logs para ver o erro específico
3. Verifique se a API está acessível publicamente

### Problema 3: Coleta não retorna dados

**Causa**: API pode não retornar dados no formato esperado

**Solução**:
1. Verifique os logs para ver a resposta da API
2. Verifique se a API requer autenticação
3. Verifique se a estrutura da resposta está correta

## 🎯 Próximos Passos

1. **Configure a URL da API no Render** (se ainda não configurou)
2. **Execute a coleta** via `/coletar-dados-ncms`
3. **Acompanhe os logs** para ver o progresso
4. **Teste o dashboard** após a coleta completar

## 📚 Documentação da API Comex Stat

Para obter a URL correta e documentação da API oficial:
- Acesse: https://comexstat.mdic.gov.br
- Verifique a documentação oficial da API
- Ou entre em contato com o MDIC para obter acesso à API

---

**Última atualização**: 05/01/2026



