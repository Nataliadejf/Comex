# Testar Banco de Dados no Render

## 🎯 Objetivo

Testar o banco de dados para diagnosticar por que não há dados no dashboard.

## 📋 Métodos Disponíveis

### Método 1: Via Endpoint HTTP (Recomendado)

1. **Acesse o Swagger:**
   ```
   https://comex-backend-wjco.onrender.com/docs
   ```

2. **Procure pelo endpoint** `GET /test/empresas`

3. **Clique em "Try it out" → "Execute"**

4. **Veja o resultado:**
   - `total_registros`: Quantidade total de registros
   - `exemplo_importadoras`: Lista de empresas importadoras
   - `exemplo_exportadoras`: Lista de empresas exportadoras

### Método 2: Via JavaScript no Console

Abra o Console do Navegador (F12) e execute:

```javascript
// Testar banco
fetch('https://comex-backend-wjco.onrender.com/test/empresas')
  .then(response => response.json())
  .then(data => {
    console.log('📊 TESTE DO BANCO:');
    console.log('Total de registros:', data.total_registros);
    console.log('Empresas importadoras:', data.exemplo_importadoras);
    console.log('Empresas exportadoras:', data.exemplo_exportadoras);
    console.log('Total importadoras distintas:', data.total_importadoras_distintas);
    console.log('Total exportadoras distintas:', data.total_exportadoras_distintas);
    
    if (data.total_registros === 0) {
      console.error('❌ BANCO ESTÁ VAZIO!');
      console.log('💡 Execute: POST /popular-dados-exemplo');
    } else if (data.total_importadoras_distintas === 0) {
      console.warn('⚠️ Nenhuma empresa importadora encontrada!');
    } else {
      console.log('✅ Banco tem dados!');
    }
  })
  .catch(error => {
    console.error('❌ Erro:', error);
  });
```

### Método 3: Testar Autocomplete Diretamente

```javascript
// Testar autocomplete importadoras
fetch('https://comex-backend-wjco.onrender.com/empresas/autocomplete/importadoras?q=Importadora&limit=10')
  .then(r => r.json())
  .then(data => {
    console.log('🔍 Autocomplete Importadoras:', data);
    if (data.length === 0) {
      console.warn('⚠️ Nenhum resultado encontrado!');
    } else {
      console.log(`✅ Encontradas ${data.length} empresas`);
    }
  });

// Testar autocomplete exportadoras
fetch('https://comex-backend-wjco.onrender.com/empresas/autocomplete/exportadoras?q=Exportadora&limit=10')
  .then(r => r.json())
  .then(data => {
    console.log('🔍 Autocomplete Exportadoras:', data);
    if (data.length === 0) {
      console.warn('⚠️ Nenhum resultado encontrado!');
    } else {
      console.log(`✅ Encontradas ${data.length} empresas`);
    }
  });
```

### Método 4: Testar Dashboard Stats

```javascript
// Testar endpoint do dashboard
fetch('https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24')
  .then(r => r.json())
  .then(data => {
    console.log('📊 Dashboard Stats:', data);
    console.log('Valor total:', data.valor_total_usd);
    console.log('Volume importações:', data.volume_importacoes);
    console.log('Volume exportações:', data.volume_exportacoes);
    
    if (data.valor_total_usd === 0) {
      console.warn('⚠️ Dashboard retornando valores zerados!');
    }
  });
```

## 🔧 Soluções Baseadas nos Resultados

### Se `total_registros === 0`:

**Banco está vazio!** Execute:

```javascript
fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ quantidade: 2000, meses: 24 })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Dados populados:', data);
  alert(`Dados criados! ${data.empresas_importadoras} importadoras, ${data.empresas_exportadoras} exportadoras`);
  window.location.reload();
});
```

### Se `total_importadoras_distintas === 0`:

**Empresas não estão sendo salvas!** Verifique:
1. Se os dados têm o campo `razao_social_importador` preenchido
2. Se o transformer está extraindo corretamente os campos de empresa
3. Se há erros nos logs do backend

### Se autocomplete retorna vazio mas há empresas:

**Problema no endpoint!** Verifique:
1. Logs do backend para erros
2. Se a query está correta
3. Se há problemas de encoding

## 📊 Checklist de Diagnóstico

Execute todos os testes acima e verifique:

- [ ] Banco tem registros? (`GET /test/empresas`)
- [ ] Há empresas importadoras? (`exemplo_importadoras`)
- [ ] Há empresas exportadoras? (`exemplo_exportadoras`)
- [ ] Autocomplete funciona? (`GET /empresas/autocomplete/importadoras?q=test`)
- [ ] Dashboard retorna dados? (`GET /dashboard/stats`)
- [ ] Logs do backend mostram erros?

## 🎯 Próximos Passos

1. **Execute os testes acima**
2. **Copie os resultados**
3. **Me informe o que encontrou**
4. **Vou corrigir baseado nos resultados**

---

**Última atualização**: 05/01/2026



