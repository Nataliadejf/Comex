# Erro: API Retorna HTML ao Invés de JSON

## 🔍 Problema

A API do Comex Stat está retornando HTML ao invés de JSON, causando o erro:
```
Attempt to decode JSON with unexpected mimetype: text/html
```

## 🔧 Possíveis Causas

### Causa 1: URL da API Incorreta

A URL `https://comexstat.mdic.gov.br/dados` pode não ser o endpoint correto da API.

**Solução:**
1. Verifique a documentação oficial do Comex Stat
2. A URL correta pode ser:
   - `https://comexstat.mdic.gov.br/api/dados`
   - `https://comexstat.mdic.gov.br/api/v1/dados`
   - Ou outra URL específica

### Causa 2: API Não Está Disponível Publicamente

A API pode não estar disponível como endpoint REST público.

**Solução:**
1. Verifique se o Comex Stat oferece uma API pública
2. Pode ser necessário:
   - Cadastro/autenticação
   - Acesso via portal web
   - Download de arquivos CSV/Excel

### Causa 3: Formato de Requisição Incorreto

A API pode esperar um formato diferente de requisição.

**Solução:**
1. Verifique a documentação da API
2. Pode ser necessário:
   - Método POST ao invés de GET
   - Headers diferentes
   - Formato de parâmetros diferente

## ✅ Soluções Implementadas

O código agora:
1. ✅ Detecta quando a API retorna HTML
2. ✅ Tenta endpoints alternativos automaticamente
3. ✅ Loga informações úteis para diagnóstico
4. ✅ Retorna lista vazia ao invés de erro (para não quebrar a coleta)

## 🔍 Próximos Passos

### Opção 1: Verificar Documentação Oficial

1. Acesse: https://comexstat.mdic.gov.br
2. Procure por "API" ou "Documentação"
3. Verifique a URL correta e formato de requisição

### Opção 2: Usar Dados de Exemplo Temporariamente

Enquanto não encontra a API correta, use dados de exemplo:

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
});
```

### Opção 3: Verificar se Existe API Pública

O Comex Stat pode não ter uma API REST pública. Nesse caso:
- Use o scraper (se disponível)
- Ou use dados de exemplo
- Ou entre em contato com o MDIC para acesso à API

## 📊 Status Atual

- ✅ Código melhorado para detectar HTML
- ✅ Tenta endpoints alternativos automaticamente
- ⚠️ API pode não estar disponível publicamente
- 💡 Verifique a documentação oficial do Comex Stat

---

**Última atualização**: 05/01/2026



