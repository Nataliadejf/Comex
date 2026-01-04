# 🔄 Explicação: Botão "Coletar Dados"

## ❓ Por que existe o botão se está conectado na API?

### Situação Atual:

O sistema tem **múltiplos métodos de obtenção de dados**:

1. **API Oficial** (`api-comexstat.mdic.gov.br`)
   - ✅ Funciona para tabela NCM (13.729 registros)
   - ⚠️ Dados mensais requerem autenticação (não disponível)

2. **Download Manual de CSV**
   - ✅ Método mais confiável atualmente
   - Requer baixar arquivos do portal manualmente
   - Processa arquivos em `D:\comex\YYYY\`

3. **Scraper Web** (se Selenium instalado)
   - Fallback se outros métodos falharem

### Função do Botão "Coletar Dados":

O botão **NÃO** coleta da API automaticamente. Ele:

1. **Verifica se já há dados** no banco
2. **Se houver dados**: Informa que a coleta via API é automática
3. **Se não houver dados**: Processa arquivos CSV existentes em `D:\comex\`

### Mudança Implementada:

- ✅ Botão renomeado para **"Processar CSV"**
- ✅ Verifica dados existentes antes de processar
- ✅ Tooltip explicativo adicionado
- ✅ Mensagens mais claras para o usuário

## 💡 Recomendação:

**Para uso com API**:
- O sistema tentará usar a API automaticamente quando disponível
- Não é necessário clicar no botão se a API estiver funcionando

**Para uso com CSV manual**:
- Baixe os arquivos CSV do portal
- Coloque em `D:\comex\YYYY\`
- Clique em "Processar CSV" para importar

## 🔄 Fluxo Automático:

```
1. Sistema inicia
   ↓
2. Tenta API oficial → Se funcionar, usa API
   ↓
3. Se API falhar → Tenta download direto
   ↓
4. Se falhar → Processa CSV em D:\comex\
   ↓
5. Se não houver CSV → Mostra mensagem para usuário
```

**O botão é apenas para processamento manual de CSV quando necessário!**



