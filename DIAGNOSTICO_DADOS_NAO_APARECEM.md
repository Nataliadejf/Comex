# Diagnóstico: Dados Não Aparecem no Dashboard

## 🔍 Problema

O dashboard está mostrando valores zerados mesmo após popular dados.

## 📋 Checklist de Diagnóstico

### 1. Verificar se há dados no banco

Execute na página `TESTAR_BANCO.html` ou via Swagger:

```javascript
// Testar banco
fetch('https://comex-backend-wjco.onrender.com/test/empresas')
  .then(r => r.json())
  .then(data => {
    console.log('📊 Total de registros:', data.total_registros);
    console.log('Valor total importações:', data.valor_total_importacoes);
    console.log('Valor total exportações:', data.valor_total_exportacoes);
    
    if (data.total_registros === 0) {
      console.error('❌ Banco está vazio!');
    } else {
      console.log('✅ Banco tem dados!');
    }
  });
```

### 2. Verificar endpoint do dashboard diretamente

```javascript
// Testar dashboard sem filtros
fetch('https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24')
  .then(r => r.json())
  .then(data => {
    console.log('📊 Dashboard Stats:', data);
    console.log('Valor total:', data.valor_total_usd);
    console.log('Volume importações:', data.volume_importacoes);
  });

// Testar dashboard com NCM específico
fetch('https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24&ncm=86079900')
  .then(r => r.json())
  .then(data => {
    console.log('📊 Dashboard Stats (NCM 86079900):', data);
  });
```

### 3. Verificar filtros aplicados

No dashboard, verifique:
- **Período**: Está dentro do período dos dados?
- **NCM**: O NCM "86079900" existe nos dados?
- **Tipo de Operação**: Está filtrando corretamente?

### 4. Verificar dados por NCM

```javascript
// Verificar se há dados para o NCM específico
fetch('https://comex-backend-wjco.onrender.com/buscar', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ncms: ["86079900"],
    page: 1,
    page_size: 10
  })
})
.then(r => r.json())
.then(data => {
  console.log('📊 Busca NCM 86079900:', data);
  console.log('Total encontrado:', data.total);
  console.log('Resultados:', data.results);
});
```

## 🔧 Possíveis Causas

### Causa 1: Banco está vazio
**Solução**: Popular dados
```javascript
fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ quantidade: 2000, meses: 24 })
});
```

### Causa 2: NCM não existe nos dados
**Solução**: 
- Remover o filtro de NCM
- Ou popular dados com esse NCM específico
- Ou usar um NCM que existe (ex: "87083090", "73182200")

### Causa 3: Período fora do range dos dados
**Solução**: 
- Ajustar o período para incluir os meses dos dados
- Ou popular dados para o período desejado

### Causa 4: Filtro de tipo de operação muito restritivo
**Solução**: 
- Remover o filtro de tipo de operação
- Ou verificar se há dados do tipo selecionado

## ✅ Solução Rápida

1. **Remover todos os filtros** no dashboard
2. **Clicar em "Buscar"**
3. Se ainda não aparecer dados, **popular dados de exemplo**:
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ quantidade: 2000, meses: 24 })
   })
   .then(r => r.json())
   .then(data => {
     alert('Dados criados! Recarregue a página.');
     window.location.reload();
   });
   ```

## 🎯 Próximos Passos

1. Execute os testes acima
2. Me informe os resultados
3. Vou corrigir baseado nos resultados

---

**Última atualização**: 05/01/2026



