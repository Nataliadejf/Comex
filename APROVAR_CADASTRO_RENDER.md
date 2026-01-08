# Como Aprovar Cadastros no Render

## 🔍 Problema

O passo a passo de aprovação não está funcionando porque precisa acessar o banco de dados diretamente.

## ✅ Solução: Usar Render Shell

### Método 1: Via Render Shell (Recomendado)

1. **Acesse o Render Dashboard:**
   - Vá para: https://dashboard.render.com
   - Clique no serviço `comex-backend`

2. **Abrir Shell:**
   - No menu lateral, clique em **"Shell"**
   - Isso abre um terminal no servidor

3. **Navegar para o diretório:**
   ```bash
   cd backend
   ```

4. **Executar script de aprovação:**
   ```bash
   python scripts/aprovar_cadastro.py listar
   ```
   
   Isso lista todos os cadastros pendentes.

5. **Aprovar por email:**
   ```bash
   python scripts/aprovar_cadastro.py aprovar nataliadejesus2@hotmail.com
   ```

6. **Ou aprovar todos:**
   ```bash
   python scripts/aprovar_cadastro.py todos
   ```

### Método 2: Criar Usuário Aprovado Diretamente

Se você quer criar um usuário já aprovado:

1. **Abrir Shell no Render:**
   - Acesse o serviço `comex-backend`
   - Clique em **"Shell"**

2. **Executar script:**
   ```bash
   cd backend
   python scripts/criar_usuario_aprovado.py
   ```

3. **Preencher os dados:**
   - Email: `nataliadejesus2@hotmail.com`
   - Senha: `senha123`
   - Nome Completo: `Natalia de Jesus`
   - (outros campos opcionais)

### Método 3: Via API (Se o endpoint estiver funcionando)

1. **Listar cadastros pendentes:**
   ```bash
   curl https://comex-backend-wjco.onrender.com/cadastros-pendentes
   ```

2. **Aprovar por token:**
   ```bash
   curl -X POST https://comex-backend-wjco.onrender.com/aprovar-cadastro \
     -H "Content-Type: application/json" \
     -d '{"token": "token_de_aprovacao"}'
   ```

## 📋 Scripts Disponíveis

### 1. `aprovar_cadastro.py`

**Comandos:**
- `listar` ou `ls` - Lista cadastros pendentes
- `aprovar <email>` - Aprova por email
- `aprovar --token <token>` - Aprova por token
- `todos` ou `all` - Aprova todos

**Exemplos:**
```bash
# Listar pendentes
python scripts/aprovar_cadastro.py listar

# Aprovar por email
python scripts/aprovar_cadastro.py aprovar usuario@email.com

# Aprovar por token
python scripts/aprovar_cadastro.py aprovar --token abc123

# Aprovar todos
python scripts/aprovar_cadastro.py todos
```

### 2. `criar_usuario_aprovado.py`

**Modo interativo:**
```bash
python scripts/criar_usuario_aprovado.py
```

**Modo linha de comando:**
```bash
python scripts/criar_usuario_aprovado.py email senha "Nome Completo" "Empresa" cpf cnpj
```

**Exemplo:**
```bash
python scripts/criar_usuario_aprovado.py nataliadejesus2@hotmail.com senha123 "Natalia de Jesus"
```

## 🔧 Resolver "Senha Incorreta"

Se aparecer "senha incorreta", pode ser:

1. **Usuário não existe no banco do Render**
   - Use `criar_usuario_aprovado.py` para criar

2. **Usuário existe mas não está aprovado**
   - Use `aprovar_cadastro.py` para aprovar

3. **Senha está incorreta**
   - Use `criar_usuario_aprovado.py` para atualizar a senha

## ✅ Checklist

- [ ] Shell do Render aberto
- [ ] Navegado para `backend/`
- [ ] Script executado
- [ ] Usuário criado/aprovado
- [ ] Login testado no frontend

---

**Última atualização**: 05/01/2026



