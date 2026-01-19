# ⚡ Como Aprovar Cadastro - Guia Rápido

## 🎯 3 Formas de Aprovar Cadastros

### **MÉTODO 1: Via API Swagger (Mais Fácil)** ⭐ RECOMENDADO

Esta é a forma mais simples e visual!

#### Passo 1: Acessar a Documentação da API

1. **Acesse**: `https://seu-backend.onrender.com/docs`
   - Substitua `seu-backend` pela URL real do seu backend no Render
   - Exemplo: `https://comex-backend-xxxxx.onrender.com/docs`

#### Passo 2: Listar Cadastros Pendentes

1. **Procure pelo endpoint**: `GET /cadastros-pendentes`
2. **Clique em**: "Try it out"
3. **Clique em**: "Execute"
4. **Você verá** uma lista com:
   - Email do usuário
   - Nome completo
   - Token de aprovação
   - Outras informações

#### Passo 3: Aprovar o Cadastro

1. **Procure pelo endpoint**: `POST /aprovar-cadastro`
2. **Clique em**: "Try it out"
3. **No campo "Request body"**, cole:
   ```json
   {
     "token": "cole_aqui_o_token_do_passo_2"
   }
   ```
4. **Clique em**: "Execute"
5. **Pronto!** ✅ O cadastro foi aprovado

---

### **MÉTODO 2: Via Render Shell** 🔧

Use este método se preferir usar comandos no terminal.

#### Passo 1: Abrir Shell no Render

1. **Render Dashboard** → `comex-backend` → **"Shell"**
2. Isso abre um terminal no servidor

#### Passo 2: Navegar e Listar

```bash
cd backend
python scripts/aprovar_cadastro.py listar
```

Isso mostra todos os cadastros pendentes com seus emails e tokens.

#### Passo 3: Aprovar

**Opção A: Por email**
```bash
python scripts/aprovar_cadastro.py aprovar email@exemplo.com
```

**Opção B: Por token**
```bash
python scripts/aprovar_cadastro.py aprovar --token token_aqui
```

**Opção C: Aprovar todos**
```bash
python scripts/aprovar_cadastro.py todos
```

---

### **MÉTODO 3: Via Endpoint Direto (curl/Postman)** 🌐

Use este método se preferir usar ferramentas externas.

#### Passo 1: Listar Pendentes

```bash
curl https://seu-backend.onrender.com/cadastros-pendentes
```

Ou use Postman:
- **GET** `https://seu-backend.onrender.com/cadastros-pendentes`

#### Passo 2: Aprovar

```bash
curl -X POST https://seu-backend.onrender.com/aprovar-cadastro \
  -H "Content-Type: application/json" \
  -d '{"token": "token_de_aprovacao_aqui"}'
```

Ou use Postman:
- **POST** `https://seu-backend.onrender.com/aprovar-cadastro`
- **Body** (JSON):
  ```json
  {
    "token": "token_de_aprovacao_aqui"
  }
  ```

---

## 📋 Resumo Rápido

### Via Swagger (Mais Fácil):
1. Acesse: `https://seu-backend.onrender.com/docs`
2. Use `GET /cadastros-pendentes` para listar
3. Use `POST /aprovar-cadastro` com o token para aprovar

### Via Shell:
```bash
cd backend
python scripts/aprovar_cadastro.py listar
python scripts/aprovar_cadastro.py aprovar email@exemplo.com
```

### Via curl:
```bash
# Listar
curl https://seu-backend.onrender.com/cadastros-pendentes

# Aprovar
curl -X POST https://seu-backend.onrender.com/aprovar-cadastro \
  -H "Content-Type: application/json" \
  -d '{"token": "token_aqui"}'
```

---

## ✅ Após Aprovar

1. **O usuário pode fazer login** normalmente
2. **Status muda** de "pendente" para "aprovado"
3. **Usuário fica ativo** (`ativo = 1`)

---

## 🐛 Problemas Comuns

### "Token inválido ou cadastro já processado"
- O token pode ter expirado (válido por 7 dias)
- O cadastro já foi aprovado anteriormente
- **Solução**: Use o método por email via Shell

### "Token expirado"
- Tokens expiram após 7 dias
- **Solução**: Use o método por email via Shell para aprovar diretamente

### Não consigo acessar `/docs`
- Verifique se o backend está online
- Verifique a URL do backend no Render Dashboard
- **Solução**: Aguarde 30-60s se o backend estiver "dormindo" (plano free)

---

## 💡 Dica

**Recomendação**: Use o **Método 1 (Swagger)** porque:
- ✅ Interface visual e fácil
- ✅ Não precisa de comandos
- ✅ Mostra todos os dados claramente
- ✅ Testa diretamente na API

---

## 📝 Exemplo Completo

### 1. Acessar Swagger
```
https://comex-backend-xxxxx.onrender.com/docs
```

### 2. Listar Pendentes
- Endpoint: `GET /cadastros-pendentes`
- Resultado:
```json
{
  "total": 1,
  "cadastros": [
    {
      "email": "teste@exemplo.com",
      "nome_completo": "Usuário Teste",
      "token_aprovacao": "abc123xyz..."
    }
  ]
}
```

### 3. Aprovar
- Endpoint: `POST /aprovar-cadastro`
- Body:
```json
{
  "token": "abc123xyz..."
}
```

### 4. Resultado
```json
{
  "message": "Cadastro aprovado com sucesso!",
  "email": "teste@exemplo.com",
  "nome": "Usuário Teste"
}
```

**Pronto!** ✅ O usuário pode fazer login agora!
