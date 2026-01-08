# Coletar Dados Reais de Todos os NCMs

## 🎯 Objetivo

Popular o dashboard com dados reais da API Comex Stat para todos os NCMs.

## 📋 Métodos Disponíveis

### Método 1: Coletar Todos os Dados (Recomendado)

Coleta dados gerais sem especificar NCMs (a API retorna todos os NCMs):

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

**Via JavaScript:**
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
});
```

### Método 2: Coletar NCMs Específicos

Se quiser coletar apenas NCMs específicos:

```javascript
fetch('https://comex-backend-wjco.onrender.com/coletar-dados-ncms', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ncms: [
      "87083090",  // Partes e acessórios para veículos
      "73182200",  // Parafusos e porcas
      "84713012",  // Notebooks
      "85171200",  // Telefones celulares
      "30049099"   // Medicamentos
    ],
    meses: 24,
    tipo_operacao: null
  })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Coleta concluída:', data);
});
```

### Método 3: Coleta Simples (Endpoint Original)

Use o endpoint original que coleta dados gerais:

```javascript
fetch('https://comex-backend-wjco.onrender.com/coletar-dados', {
  method: 'POST'
})
.then(r => r.json())
.then(data => {
  console.log('✅ Coleta concluída:', data);
});
```

## ⏰ Tempo Estimado

- **Coleta geral (todos NCMs)**: 30-60 minutos (dependendo da API)
- **Coleta de NCMs específicos**: 5-10 minutos por NCM
- **Coleta automática**: Diária às 02:00

## ⚠️ Importante

1. **API Comex Stat**: 
   - Pode ter rate limiting
   - Pode estar temporariamente indisponível
   - Requer configuração correta de `COMEX_STAT_API_URL` e `COMEX_STAT_API_KEY`

2. **Verificar Configuração**:
   - No Render Dashboard → `comex-backend` → "Environment"
   - Verifique se `COMEX_STAT_API_URL` está configurada
   - Verifique se `COMEX_STAT_API_KEY` está configurada (pode estar vazia)

3. **Monitorar Coleta**:
   - Acesse os logs do backend no Render
   - Procure por mensagens de progresso
   - Verifique se há erros

## 🔧 NCMs Mais Importantes (Opcional)

Se quiser coletar apenas os NCMs mais importantes:

```javascript
const ncmsImportantes = [
  "87083090",  // Partes e acessórios para veículos automóveis
  "73182200",  // Parafusos e porcas de ferro ou aço
  "84713012",  // Notebooks
  "85171200",  // Telefones celulares
  "30049099",  // Medicamentos
  "27090000",  // Óleo cru de petróleo
  "10019000",  // Trigo
  "02012000",  // Carne bovina
  "09011100",  // Café não torrado
  "15091000"   // Óleo de oliva
];

fetch('https://comex-backend-wjco.onrender.com/coletar-dados-ncms', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ncms: ncmsImportantes,
    meses: 24
  })
});
```

## 📊 Verificar Resultados

Após a coleta, verifique:

1. **Testar banco:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/test/empresas')
     .then(r => r.json())
     .then(data => {
       console.log('Total de registros:', data.total_registros);
     });
   ```

2. **Testar dashboard:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24')
     .then(r => r.json())
     .then(data => {
       console.log('Valor total:', data.valor_total_usd);
     });
   ```

## 🎯 Recomendação

1. **Primeira coleta**: Use `POST /coletar-dados-ncms` com `ncms: null` para coletar todos os dados
2. **Coletas subsequentes**: A coleta automática diária manterá os dados atualizados
3. **NCMs específicos**: Use apenas se precisar de dados muito específicos

---

**Última atualização**: 05/01/2026



