# Testar Autocomplete e Coleta de Dados

## 🔍 Problema 1: Autocomplete Não Funciona

### Diagnóstico:

1. **Verificar se há dados no banco:**
   ```javascript
   // No console do navegador (F12)
   fetch('https://comex-backend-wjco.onrender.com/test/empresas')
     .then(r => r.json())
     .then(data => {
       console.log('📊 Dados no banco:', data);
       console.log('Total de registros:', data.total_registros);
       console.log('Exemplo importadoras:', data.exemplo_importadoras);
       console.log('Exemplo exportadoras:', data.exemplo_exportadoras);
     });
   ```

2. **Testar autocomplete diretamente:**
   ```javascript
   // Testar importadoras
   fetch('https://comex-backend-wjco.onrender.com/empresas/autocomplete/importadoras?q=Importadora&limit=10')
     .then(r => r.json())
     .then(data => {
       console.log('✅ Resultado autocomplete:', data);
     });
   
   // Testar exportadoras
   fetch('https://comex-backend-wjco.onrender.com/empresas/autocomplete/exportadoras?q=Exportadora&limit=10')
     .then(r => r.json())
     .then(data => {
       console.log('✅ Resultado autocomplete:', data);
     });
   ```

3. **Verificar logs do backend:**
   - No Render Dashboard → `comex-backend` → "Logs"
   - Procure por: `🔍 Buscando importadoras` ou `🔍 Buscando exportadoras`

### Solução:

**Se não houver dados no banco:**
1. Popular com dados de exemplo:
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ quantidade: 1000, meses: 24 })
   })
   .then(r => r.json())
   .then(data => {
     console.log('✅ Dados populados:', data);
     alert(`Dados criados! ${data.empresas_importadoras} importadoras, ${data.empresas_exportadoras} exportadoras`);
   });
   ```

**Se houver dados mas autocomplete não funcionar:**
1. Verificar console do navegador (F12) para erros
2. Verificar se a resposta da API está correta
3. Verificar se o frontend está fazendo a requisição corretamente

---

## 🔍 Problema 2: Coleta de Dados Não Retorna Dados no Dashboard

### Diagnóstico:

1. **Verificar se a coleta funcionou:**
   ```javascript
   // Verificar dados no banco
   fetch('https://comex-backend-wjco.onrender.com/test/empresas')
     .then(r => r.json())
     .then(data => {
       console.log('📊 Total de registros:', data.total_registros);
       if (data.total_registros === 0) {
         console.log('⚠️ Banco está vazio!');
       }
     });
   ```

2. **Verificar logs da coleta:**
   - No Render Dashboard → `comex-backend` → "Logs"
   - Procure por:
     - `Coleta de dados iniciada`
     - `Registros coletados`
     - `Erro ao coletar`

3. **Testar coleta manualmente:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/coletar-dados', {
     method: 'POST'
   })
   .then(r => r.json())
   .then(data => {
     console.log('✅ Resultado da coleta:', data);
     console.log('Total de registros:', data.stats?.total_registros);
     console.log('Meses processados:', data.stats?.meses_processados);
     console.log('Erros:', data.stats?.erros);
   });
   ```

4. **Verificar dashboard stats:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24')
     .then(r => r.json())
     .then(data => {
       console.log('📊 Dashboard stats:', data);
       console.log('Valor total:', data.valor_total_usd);
       console.log('Volume importações:', data.volume_importacoes);
     });
   ```

### Solução:

**Se a coleta não retornou dados:**

1. **A API Comex Stat pode não estar disponível:**
   - A coleta depende da API externa
   - Pode ter rate limiting
   - Pode estar temporariamente indisponível

2. **Usar dados de exemplo temporariamente:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ quantidade: 2000, meses: 24 })
   })
   .then(r => r.json())
   .then(data => {
     console.log('✅ Dados populados:', data);
     alert('Dados criados! Recarregue o dashboard.');
     window.location.reload();
   });
   ```

3. **Verificar configuração da API:**
   - No Render Dashboard → `comex-backend` → "Environment"
   - Verificar `COMEX_STAT_API_URL` e `COMEX_STAT_API_KEY`

**Se o dashboard não mostra dados mesmo com dados no banco:**

1. Verificar filtros aplicados no dashboard
2. Verificar se o período está correto
3. Verificar console do navegador para erros
4. Testar endpoint diretamente (ver acima)

---

## ✅ Checklist de Testes

- [ ] Banco tem dados? (`GET /test/empresas`)
- [ ] Autocomplete funciona? (`GET /empresas/autocomplete/importadoras?q=test`)
- [ ] Coleta retornou dados? (`POST /coletar-dados`)
- [ ] Dashboard mostra dados? (`GET /dashboard/stats`)
- [ ] Logs do backend mostram erros?
- [ ] Console do navegador mostra erros?

---

## 🎯 Próximos Passos

1. **Execute os testes acima**
2. **Verifique os resultados**
3. **Me informe o que encontrou**
4. **Vou corrigir baseado nos resultados**

---

**Última atualização**: 05/01/2026

