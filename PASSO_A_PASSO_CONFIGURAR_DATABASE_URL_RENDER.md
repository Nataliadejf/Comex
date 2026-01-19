# 📋 Passo a Passo: Configurar DATABASE_URL no Render

## 🎯 Objetivo
Configurar a variável de ambiente `DATABASE_URL` no Render para que o script local importe os dados diretamente no PostgreSQL do Render.

---

## 📍 Passo 1: Acessar o Dashboard do Render

1. Abra seu navegador
2. Acesse: **https://dashboard.render.com**
3. Faça login na sua conta

---

## 📍 Passo 2: Encontrar o Banco PostgreSQL

### Opção A: Se você já tem um PostgreSQL criado

1. No menu lateral esquerdo, clique em **"PostgreSQL"** ou procure na lista de serviços
2. Clique no nome do seu banco PostgreSQL (ex: `comex-database` ou `comexdb`)

### Opção B: Se você NÃO tem PostgreSQL ainda

1. No Dashboard, clique no botão **"New +"** (canto superior direito)
2. Selecione **"PostgreSQL"**
3. Preencha:
   - **Name:** `comex-database` (ou outro nome de sua escolha)
   - **Database:** `comexdb` (ou outro nome)
   - **User:** Deixe o padrão ou escolha um nome
   - **Region:** Escolha a região mais próxima (ex: `Oregon (US West)`)
   - **PostgreSQL Version:** Deixe a versão mais recente
   - **Plan:** Escolha o plano (Free tier funciona para testes)
4. Clique em **"Create Database"**
5. Aguarde alguns minutos até o banco ser criado

---

## 📍 Passo 3: Copiar a Internal Database URL

1. Com o PostgreSQL selecionado, você verá várias abas no topo
2. Clique na aba **"Connections"** ou **"Info"**
3. Procure por **"Internal Database URL"** ou **"Connection String"**
4. Você verá algo assim:
   ```
   postgres://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
   ```
5. **Clique no ícone de copiar** ao lado da URL (ou selecione e copie com Ctrl+C)
6. ⚠️ **IMPORTANTE:** Guarde esta URL em local seguro (contém senha!)

---

## 📍 Passo 4: Converter para Formato PostgreSQL

O Render pode fornecer a URL com `postgres://`, mas precisamos `postgresql://`:

- Se a URL começar com `postgres://`, substitua por `postgresql://`
- Exemplo:
  ```
  postgres://user:pass@host:5432/db
  ```
  Vira:
  ```
  postgresql://user:pass@host:5432/db
  ```

**Nota:** O script já faz essa conversão automaticamente, mas é bom verificar.

---

## 📍 Passo 5: Configurar no Serviço Backend

1. No Dashboard do Render, vá em **"Web Services"** ou procure pelo seu serviço backend
2. Clique no nome do seu serviço backend (ex: `comex-backend`)
3. No menu lateral esquerdo, clique em **"Environment"** (Variáveis de Ambiente)
4. Você verá uma lista de variáveis de ambiente

### Se DATABASE_URL já existe:

1. Encontre a linha com `DATABASE_URL`
2. Clique no **valor atual** (pode estar vazio ou com valor incorreto)
3. Cole a URL do PostgreSQL que você copiou (Passo 3)
4. Pressione **Enter** ou clique em **"Save Changes"**

### Se DATABASE_URL NÃO existe:

1. Clique no botão **"Add Environment Variable"** ou **"Add Variable"**
2. No campo **"Key"**, digite: `DATABASE_URL`
3. No campo **"Value"**, cole a URL do PostgreSQL que você copiou
4. Clique em **"Save Changes"** ou **"Add"**

---

## 📍 Passo 6: Verificar Configuração

1. Após salvar, verifique se a variável aparece na lista
2. A URL deve começar com `postgresql://` ou `postgres://`
3. Deve ter pelo menos 50-100 caracteres
4. Deve conter `@` (separando credenciais do host)

---

## 📍 Passo 7: Usar no Script Local

Agora você pode usar a mesma URL no script local:

### Opção A: Variável de Ambiente (PowerShell)

```powershell
# Cole a URL completa aqui (substitua pela sua URL real)
$env:DATABASE_URL = "postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb"

# Verificar qual banco está sendo usado
python -c "import os; from pathlib import Path; import sys; sys.path.insert(0, 'backend'); from database.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); result = db.execute(text('SELECT COUNT(*) FROM operacoes_comex')); print(f'Registros: {result.scalar()}'); db.close()"

# Se mostrar 0, está conectado ao Render (correto!)
# Agora importe os dados:
python importar_excel_local.py "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
```

### Opção B: Arquivo .env

1. Na raiz do projeto, crie um arquivo chamado `.env`
2. Adicione a linha:
   ```
   DATABASE_URL=postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
   ```
3. Substitua pela sua URL real
4. Salve o arquivo
5. Execute o script normalmente:
   ```powershell
   python importar_excel_local.py "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
   ```

---

## ✅ Checklist de Verificação

- [ ] PostgreSQL criado no Render
- [ ] Internal Database URL copiada
- [ ] URL convertida para `postgresql://` (se necessário)
- [ ] DATABASE_URL configurada no serviço backend do Render
- [ ] DATABASE_URL configurada localmente (variável de ambiente ou .env)
- [ ] Teste de conexão executado e mostra 0 registros (banco vazio do Render)
- [ ] Script de importação executado com sucesso

---

## 🔍 Como Verificar se Está Funcionando

### 1. Teste Local (Antes de Importar)

```powershell
python -c "import os; from pathlib import Path; import sys; sys.path.insert(0, 'backend'); from database.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); result = db.execute(text('SELECT COUNT(*) FROM operacoes_comex')); print(f'Registros: {result.scalar()}'); db.close()"
```

**Resultado esperado:** `Registros: 0` (banco vazio do Render)

### 2. Após Importação

```powershell
# Verificar no Render via API
Invoke-WebRequest -Uri "https://comex-backend-gecp.onrender.com/validar-sistema" -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select-Object -ExpandProperty banco_dados | ConvertTo-Json -Depth 5
```

**Resultado esperado:** Mostrar os registros importados (ex: `total_operacoes_comex: 51161`)

---

## 🐛 Troubleshooting

### Problema: "DATABASE_URL não encontrada"

**Solução:**
- Verifique se você está no serviço correto (backend, não frontend)
- Verifique se o nome está exatamente `DATABASE_URL` (maiúsculas)
- Recarregue a página do Dashboard

### Problema: "Connection refused" ou "Could not connect"

**Solução:**
- Verifique se o PostgreSQL está rodando (status deve ser "Available")
- Verifique se copiou a **Internal Database URL** (não External)
- Verifique se a URL está completa (não cortada)

### Problema: "Invalid URL format"

**Solução:**
- Certifique-se que a URL começa com `postgresql://` ou `postgres://`
- Verifique se não há espaços extras antes/depois da URL
- Verifique se a URL não foi quebrada em múltiplas linhas

### Problema: Script ainda usa SQLite local

**Solução:**
- Verifique se configurou `$env:DATABASE_URL` antes de executar o script
- Ou verifique se o arquivo `.env` existe e tem a URL correta
- Execute o teste de conexão para confirmar qual banco está sendo usado

---

## 📸 Exemplo Visual

### Como deve aparecer no Render:

```
Environment Variables
┌─────────────────────┬──────────────────────────────────────────────┐
│ Key                 │ Value                                         │
├─────────────────────┼──────────────────────────────────────────────┤
│ DATABASE_URL        │ postgresql://user:pass@host:5432/db          │
│ ENVIRONMENT         │ production                                    │
│ PYTHON_VERSION      │ 3.11                                         │
└─────────────────────┴──────────────────────────────────────────────┘
```

---

## 🔒 Segurança

⚠️ **IMPORTANTE:**
- **NÃO** compartilhe a DATABASE_URL publicamente
- **NÃO** faça commit do arquivo `.env` no Git
- Adicione `.env` ao `.gitignore` se ainda não estiver
- A URL contém credenciais sensíveis (usuário e senha)

---

## 📞 Próximos Passos

Após configurar a DATABASE_URL:

1. ✅ Testar conexão local
2. ✅ Importar Excel Comex
3. ✅ Importar CNAE
4. ✅ Verificar dados no Render
5. ✅ Executar enriquecimento
6. ✅ Verificar dashboard

---

## 🔗 Links Úteis

- **Render Dashboard:** https://dashboard.render.com
- **Documentação Render:** https://render.com/docs
- **PostgreSQL no Render:** https://render.com/docs/databases
