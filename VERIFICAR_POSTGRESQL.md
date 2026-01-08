# Verificar Configuração do PostgreSQL

## 🔍 Como Verificar se o PostgreSQL está Configurado Corretamente

### Método 1: Via Health Check da API

1. **Teste o endpoint `/health`:**
   ```
   https://comex-3.onrender.com/health
   ```
   
   **Resposta esperada:**
   ```json
   {
     "status": "healthy",
     "database": "connected"
   }
   ```

2. **Se retornar `"database": "disconnected"`:**
   - Verifique se `DATABASE_URL` está configurada
   - Verifique os logs do serviço para erros de conexão

### Método 2: Via Logs do Render

1. **Acesse o serviço no Render Dashboard**
2. **Vá em "Logs"**
3. **Procure por:**
   - ✅ `Banco de dados inicializado`
   - ✅ `Connected to database`
   - ✅ `Application startup complete`
   - ❌ `Database connection failed`
   - ❌ `password authentication failed`

### Método 3: Testar Endpoint que Usa o Banco

1. **Teste o endpoint `/dashboard/stats`:**
   ```
   https://comex-3.onrender.com/dashboard/stats?meses=12
   ```
   
2. **Se retornar dados (mesmo que vazio):**
   - ✅ Banco está conectado e funcionando
   
3. **Se retornar erro 500:**
   - ❌ Verifique os logs para identificar o problema

### Método 4: Verificar Variáveis de Ambiente

1. **No Render Dashboard:**
   - Acesse o serviço (Comex-3 ou Comex-2)
   - Vá em **"Environment"**
   - Verifique se `DATABASE_URL` está configurada
   - A URL deve começar com `postgresql://`

### Método 5: Verificar Status do PostgreSQL

1. **No Render Dashboard:**
   - Acesse o PostgreSQL (`comex-database`)
   - Verifique se o status é **"Available"**
   - Se estiver **"Paused"**, clique em **"Resume"**

## ✅ Checklist de Verificação

- [ ] PostgreSQL está com status "Available"
- [ ] `DATABASE_URL` está configurada nos serviços
- [ ] Health check retorna `"database": "connected"`
- [ ] Logs não mostram erros de conexão
- [ ] Endpoints da API estão funcionando
- [ ] Tabelas foram criadas (verificar via logs ou API)

## 🐛 Problemas Comuns

### Problema: Health check retorna "disconnected"

**Solução:**
1. Verifique se `DATABASE_URL` está configurada
2. Confirme que está usando a Internal Database URL
3. Verifique se o PostgreSQL está rodando
4. Veja os logs para mais detalhes

### Problema: Erro "relation does not exist"

**Solução:**
1. As tabelas são criadas automaticamente no startup
2. Verifique os logs para confirmar que `init_db()` foi executado
3. Se necessário, faça um novo deploy

### Problema: Erro de autenticação

**Solução:**
1. Copie novamente a Internal Database URL do Render
2. Certifique-se de copiar a URL completa
3. Não modifique a URL manualmente

---

**Última atualização**: 05/01/2026



