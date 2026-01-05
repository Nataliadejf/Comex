# Verificar Configuração da API Comex Stat

## 🔍 Verificar se a API Está Configurada

### Método 1: Verificar Variáveis no Render

1. **Acesse o Render Dashboard:**
   - Vá em `comex-backend` → "Environment"

2. **Verifique se existem:**
   - `COMEX_STAT_API_URL` - URL da API
   - `COMEX_STAT_API_KEY` - Chave da API (pode estar vazia)

3. **Se não existirem, adicione:**
   - Clique em "Add Environment Variable"
   - Nome: `COMEX_STAT_API_URL`
   - Valor: `https://comexstat.mdic.gov.br` (ou a URL correta da API)
   - Salve

### Método 2: Verificar Logs do Backend

No Render Dashboard → `comex-backend` → "Logs":
- Procure por: `API do Comex Stat não configurada`
- Ou: `API do Comex Stat acessível`

### Método 3: Testar Endpoint de Coleta

```javascript
// Testar se a API está configurada
fetch('https://comex-backend-wjco.onrender.com/coletar-dados-ncms', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ncms: null,
    meses: 1,  // Apenas 1 mês para teste rápido
    tipo_operacao: "Importação"
  })
})
.then(r => r.json())
.then(data => {
  console.log('Resultado:', data);
  if (data.stats?.erros?.includes('API do Comex Stat não está disponível')) {
    console.error('❌ API não configurada!');
  } else {
    console.log('✅ Coleta iniciada!');
  }
});
```

## 🔧 Configurar API no Render

### Passo a Passo:

1. **Acesse Render Dashboard:**
   - https://dashboard.render.com

2. **Vá para o serviço:**
   - Clique em `comex-backend`

3. **Acesse Environment:**
   - Menu lateral → "Environment"

4. **Adicione variáveis:**
   - Clique em "Add Environment Variable"
   - **Variável 1:**
     - Key: `COMEX_STAT_API_URL`
     - Value: `https://comexstat.mdic.gov.br` (ou URL correta)
   - **Variável 2:**
     - Key: `COMEX_STAT_API_KEY`
     - Value: (deixe vazio ou adicione se tiver chave)

5. **Salve e reinicie:**
   - Clique em "Save Changes"
   - O serviço será reiniciado automaticamente

## ⚠️ Importante

- **A URL da API pode variar** - verifique a documentação oficial do Comex Stat
- **A API pode ser pública** - nesse caso, `COMEX_STAT_API_KEY` pode ficar vazio
- **A API pode requerer autenticação** - nesse caso, você precisa da chave

## 🎯 Após Configurar

1. **Aguarde o serviço reiniciar** (1-2 minutos)
2. **Execute a coleta** via `/coletar-dados-ncms`
3. **Acompanhe os logs** para ver se está funcionando

---

**Última atualização**: 05/01/2026

