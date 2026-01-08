# Popular Dados no Render - Sem Shell

## 🔍 Problema

O dashboard está funcionando, mas não mostra dados porque o banco de dados está vazio.

## ✅ Solução: Endpoint para Popular Dados

Como não temos acesso ao Shell (requer upgrade), vou criar um endpoint HTTP para popular dados.

## 📋 Métodos Disponíveis

### Método 1: Via Endpoint HTTP (Recomendado)

1. **Acesse o Swagger:**
   ```
   https://comex-backend-wjco.onrender.com/docs
   ```

2. **Procure pelo endpoint** `POST /popular-dados-exemplo`

3. **Clique em "Try it out"**

4. **Preencha:**
   - `quantidade`: `100` (ou outro número)
   - `meses`: `24` (últimos 24 meses)

5. **Clique em "Execute"**

### Método 2: Via JavaScript no Console

Abra o Console do Navegador (F12) e execute:

```javascript
fetch('https://comex-backend-wjco.onrender.com/popular-dados-exemplo', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    quantidade: 100,
    meses: 24
  })
})
.then(response => response.json())
.then(data => {
  console.log('✅ Dados populados:', data);
  alert('Dados criados! Recarregue o dashboard.');
})
.catch(error => {
  console.error('❌ Erro:', error);
  alert('Erro: ' + error.message);
});
```

### Método 3: Via cURL

```bash
curl -X POST https://comex-backend-wjco.onrender.com/popular-dados-exemplo \
  -H "Content-Type: application/json" \
  -d '{"quantidade": 100, "meses": 24}'
```

## 🎯 Após Popular Dados

1. **Recarregue o dashboard** (F5)
2. **Os dados devem aparecer** nos gráficos e tabelas
3. **Teste os filtros** para ver se funcionam

## 📊 Quantidade Recomendada

- **100 registros**: Teste rápido
- **500 registros**: Boa quantidade para testes
- **1000+ registros**: Dados mais realistas

## ⚠️ Importante

- Os dados são gerados aleatoriamente para teste
- Não são dados reais da API Comex
- Para dados reais, você precisa configurar a coleta automática

---

**Última atualização**: 05/01/2026



