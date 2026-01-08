# Criar Usuário sem Shell (Plano Free)

## ⚠️ Problema

O Shell no Render requer upgrade para plano Starter. No plano Free, não temos acesso ao Shell.

## ✅ Solução: Endpoint HTTP

Criei um endpoint especial que permite criar usuários aprovados diretamente via HTTP, sem precisar do Shell!

## 📋 Como Usar

### Método 1: Via Navegador (Mais Fácil)

1. **Acesse o endpoint:**
   ```
   https://comex-backend-wjco.onrender.com/criar-usuario-teste
   ```

2. **Você verá um formulário** (se o navegador suportar)
   - Preencha: Email, Senha, Nome Completo
   - Clique em Submit

### Método 2: Via cURL (Linha de Comando)

Execute no terminal:

```bash
curl -X POST https://comex-backend-wjco.onrender.com/criar-usuario-teste \
  -F "email=nataliadejesus2@hotmail.com" \
  -F "senha=senha123" \
  -F "nome_completo=Natalia de Jesus"
```

### Método 3: Via Postman ou Insomnia

1. **Método:** POST
2. **URL:** `https://comex-backend-wjco.onrender.com/criar-usuario-teste`
3. **Body Type:** form-data
4. **Campos:**
   - `email`: `nataliadejesus2@hotmail.com`
   - `senha`: `senha123`
   - `nome_completo`: `Natalia de Jesus`

### Método 4: Via JavaScript no Console do Navegador

Abra o Console do Navegador (F12) e execute:

```javascript
fetch('https://comex-backend-wjco.onrender.com/criar-usuario-teste', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    email: 'nataliadejesus2@hotmail.com',
    senha: 'senha123',
    nome_completo: 'Natalia de Jesus'
  })
})
.then(response => response.json())
.then(data => console.log('✅ Usuário criado:', data))
.catch(error => console.error('❌ Erro:', error));
```

## 🎯 Exemplo Completo

### Criar Usuário de Teste:

```bash
curl -X POST https://comex-backend-wjco.onrender.com/criar-usuario-teste \
  -F "email=nataliadejesus2@hotmail.com" \
  -F "senha=senha123" \
  -F "nome_completo=Natalia de Jesus"
```

**Resposta esperada:**
```json
{
  "message": "Usuário criado e aprovado com sucesso",
  "email": "nataliadejesus2@hotmail.com",
  "status": "aprovado"
}
```

## ✅ Após Criar o Usuário

1. **Acesse o frontend:**
   ```
   https://comex-4.onrender.com/login
   ```

2. **Faça login:**
   - Email: `nataliadejesus2@hotmail.com`
   - Senha: `senha123`

3. **Deve funcionar!** ✅

## 🔧 Outras Opções

### Aprovar Cadastro Existente

Se você já tem um cadastro pendente, use o endpoint de aprovação:

```bash
curl -X POST https://comex-backend-wjco.onrender.com/aprovar-cadastro \
  -H "Content-Type: application/json" \
  -d '{"token": "token_de_aprovacao"}'
```

### Listar Cadastros Pendentes

```bash
curl https://comex-backend-wjco.onrender.com/cadastros-pendentes
```

## ⚠️ Importante

- Este endpoint cria usuários **já aprovados** automaticamente
- Em produção, considere proteger este endpoint com autenticação admin
- Por enquanto, está aberto para facilitar testes

## 📋 Checklist

- [ ] Backend está rodando (verificar `/health`)
- [ ] Endpoint `/criar-usuario-teste` chamado
- [ ] Usuário criado com sucesso
- [ ] Login testado no frontend
- [ ] Funcionando! ✅

---

**Última atualização**: 05/01/2026



