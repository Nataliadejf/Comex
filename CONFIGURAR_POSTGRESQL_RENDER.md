# Configurar PostgreSQL no Render - Passo a Passo

## 🎯 Objetivo

Configurar o banco de dados PostgreSQL no Render e conectar aos serviços Comex-3 e Comex-2.

## 📋 Passo a Passo Completo

### PASSO 1: Criar Banco de Dados PostgreSQL no Render

1. **Acesse o Render Dashboard:**
   - Vá para: https://dashboard.render.com
   - Faça login na sua conta

2. **Criar Novo PostgreSQL:**
   - Clique no botão **"+ New"** (canto superior direito)
   - Selecione **"PostgreSQL"** na lista de opções

3. **Configurar o Banco de Dados:**
   - **Name**: `comex-database` (ou outro nome de sua preferência)
   - **Database**: `comex_db` (nome do banco de dados)
   - **User**: `comex_user` (nome do usuário)
   - **Region**: `Oregon` (mesma região dos seus serviços)
   - **PostgreSQL Version**: `15` (ou a versão mais recente disponível)
   - **Plan**: `Free` (para começar, pode fazer upgrade depois)

4. **Criar o Banco:**
   - Clique em **"Create Database"**
   - Aguarde 1-2 minutos para o PostgreSQL ser criado

### PASSO 2: Copiar a URL de Conexão

Após criar o PostgreSQL:

1. **Acesse o PostgreSQL criado:**
   - Clique no nome do banco de dados (`comex-database`)

2. **Copiar a Internal Database URL:**
   - Na página do PostgreSQL, procure por **"Internal Database URL"**
   - Clique no botão **"Copy"** ao lado da URL
   - A URL terá o formato:
     ```
     postgresql://usuario:senha@host:porta/database
     ```
   - **IMPORTANTE**: Use a **Internal Database URL** (não a External), pois seus serviços estão na mesma região

### PASSO 3: Configurar Comex-3

1. **Acesse o serviço Comex-3:**
   - No Render Dashboard, clique em **"Comex-3"**

2. **Ir para Environment Variables:**
   - No menu lateral esquerdo, clique em **"Environment"**

3. **Adicionar/Atualizar DATABASE_URL:**
   - Procure por `DATABASE_URL` na lista de variáveis
   - Se existir, clique em **"Edit"** (ícone de lápis)
   - Se não existir, clique em **"+ Add Environment Variable"**
   - **Key**: `DATABASE_URL`
   - **Value**: Cole a **Internal Database URL** que você copiou no Passo 2
   - Clique em **"Save Changes"**

4. **Verificar outras variáveis necessárias:**
   Certifique-se de que estas variáveis também estão configuradas:
   - `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`
   - `COMEX_STAT_API_KEY` = (deixe vazio)
   - `SECRET_KEY` = (deve ter uma chave gerada)
   - `ENVIRONMENT` = `production`
   - `DEBUG` = `false`
   - `PYTHON_VERSION` = `3.11`

### PASSO 4: Configurar Comex-2

Repita o Passo 3 para o serviço **Comex-2**:

1. Acesse **"Comex-2"**
2. Vá em **"Environment"**
3. Adicione/Atualize `DATABASE_URL` com a mesma URL do PostgreSQL
4. Verifique as outras variáveis de ambiente

### PASSO 5: Fazer Deploy dos Serviços

Após configurar as variáveis de ambiente:

1. **Para Comex-3:**
   - No serviço Comex-3, clique em **"Manual Deploy"**
   - Selecione **"Deploy latest commit"**
   - Aguarde o deploy completar (5-10 minutos)

2. **Para Comex-2:**
   - No serviço Comex-2, clique em **"Manual Deploy"**
   - Selecione **"Deploy latest commit"**
   - Aguarde o deploy completar

### PASSO 6: Verificar Logs

Após o deploy:

1. **Verificar Logs do Comex-3:**
   - No serviço Comex-3, vá em **"Logs"** (menu lateral)
   - Procure por mensagens como:
     - ✅ `Banco de dados inicializado`
     - ✅ `Application startup complete`
     - ✅ `Connected to database`
     - ❌ Se houver erros de conexão, verifique a `DATABASE_URL`

2. **Verificar Logs do Comex-2:**
   - Repita o processo para Comex-2

### PASSO 7: Testar Conexão com o Banco

1. **Testar Health Check:**
   - Acesse: `https://comex-3.onrender.com/health`
   - Deve retornar:
     ```json
     {
       "status": "healthy",
       "database": "connected"
     }
     ```

2. **Se retornar erro:**
   - Verifique os logs do serviço
   - Confirme que a `DATABASE_URL` está correta
   - Verifique se o PostgreSQL está rodando (status deve ser "Available")

### PASSO 8: Verificar Criação das Tabelas

O backend cria automaticamente as tabelas na inicialização. Para verificar:

1. **No Render Dashboard:**
   - Acesse o PostgreSQL (`comex-database`)
   - Vá em **"Connect"** ou **"Info"**
   - Você pode usar o **"psql"** ou um cliente PostgreSQL externo

2. **Ou verificar via API:**
   - Teste um endpoint que usa o banco, como `/dashboard/stats`
   - Se retornar dados (mesmo que vazio), significa que as tabelas foram criadas

## ✅ Checklist

- [ ] PostgreSQL criado no Render
- [ ] Internal Database URL copiada
- [ ] `DATABASE_URL` configurada no Comex-3
- [ ] `DATABASE_URL` configurada no Comex-2
- [ ] Todas as variáveis de ambiente verificadas
- [ ] Deploy realizado no Comex-3
- [ ] Deploy realizado no Comex-2
- [ ] Logs verificados (sem erros de conexão)
- [ ] Health check retornando `"database": "connected"`
- [ ] Tabelas criadas automaticamente

## 🔧 Troubleshooting

### Erro: "Database connection failed"

**Possíveis causas:**
1. `DATABASE_URL` não está configurada
2. URL incorreta (usou External ao invés de Internal)
3. PostgreSQL não está rodando
4. Credenciais incorretas

**Solução:**
- Verifique se a `DATABASE_URL` está configurada corretamente
- Use a **Internal Database URL** (não a External)
- Confirme que o PostgreSQL está com status "Available"

### Erro: "relation does not exist"

**Causa:** Tabelas não foram criadas

**Solução:**
- O backend cria as tabelas automaticamente no startup
- Verifique os logs para ver se `init_db()` foi executado
- Se necessário, faça um novo deploy

### Erro: "password authentication failed"

**Causa:** Credenciais incorretas na URL

**Solução:**
- Copie novamente a Internal Database URL do Render
- Certifique-se de copiar a URL completa, incluindo senha

## 📝 Notas Importantes

1. **Internal vs External URL:**
   - Use sempre a **Internal Database URL** para serviços na mesma região
   - A External URL é para conexões de fora do Render

2. **Criação Automática de Tabelas:**
   - O backend cria todas as tabelas automaticamente na inicialização
   - Não é necessário executar scripts SQL manualmente

3. **Backup:**
   - O plano Free do Render não inclui backups automáticos
   - Considere fazer upgrade para plano pago se precisar de backups

4. **Limites do Plano Free:**
   - PostgreSQL Free tem limite de 90 dias
   - Após 90 dias de inatividade, o banco pode ser deletado
   - Considere fazer upgrade se precisar de persistência garantida

## 🎯 Próximos Passos

Após configurar o PostgreSQL:

1. ✅ Testar login no frontend
2. ✅ Testar cadastro de usuários
3. ✅ Popular o banco com dados de exemplo (se necessário)
4. ✅ Configurar coletas automáticas de dados
5. ✅ Monitorar uso do banco de dados

---

**Última atualização**: 05/01/2026



