# Verificar Notificações de Email e Aprovação

## ⚠️ Importante: Emails Não São Enviados Realmente

O sistema **não envia emails reais** por enquanto. As notificações aparecem apenas nos **logs do backend**.

## 📋 Como Verificar Notificações

### Método 1: Ver Logs do Backend (Recomendado)

1. **No Render Dashboard:**
   - Acesse o serviço `comex-backend`
   - Clique em **"Logs"** (menu lateral)

2. **Procure por:**
   - `📧 SOLICITAÇÃO DE APROVAÇÃO DE CADASTRO`
   - `📧 CADASTRO APROVADO`
   - `Token de aprovação:`

3. **Copie o token** que aparece nos logs

### Método 2: Listar Cadastros Pendentes

1. **Via Swagger:**
   - Acesse: `https://comex-backend-wjco.onrender.com/docs`
   - Procure por `GET /cadastros-pendentes`
   - Clique em "Try it out" → "Execute"
   - Você verá todos os cadastros pendentes com seus tokens

2. **Via JavaScript:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/cadastros-pendentes')
     .then(response => response.json())
     .then(data => {
       console.log('Cadastros pendentes:', data);
       data.cadastros.forEach(c => {
         console.log(`Email: ${c.email}, Token: ${c.token_aprovacao}`);
       });
     });
   ```

## ✅ Como Aprovar Cadastros

### Método 1: Via Endpoint HTTP

1. **Obtenha o token** dos logs ou do endpoint `/cadastros-pendentes`

2. **Aprove via Swagger:**
   - Acesse: `https://comex-backend-wjco.onrender.com/docs`
   - Procure por `POST /aprovar-cadastro`
   - Body: `{"token": "token_aqui"}`
   - Execute

3. **Ou via JavaScript:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/aprovar-cadastro', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ token: 'token_aqui' })
   })
   .then(response => response.json())
   .then(data => {
     console.log('✅ Cadastro aprovado:', data);
     alert('Cadastro aprovado!');
   });
   ```

### Método 2: Criar Usuário Já Aprovado

Use o endpoint `/criar-usuario-teste` para criar usuários já aprovados:

```javascript
fetch('https://comex-backend-wjco.onrender.com/criar-usuario-teste', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    email: 'usuario@email.com',
    senha: 'senha123',
    nome_completo: 'Nome Completo'
  })
});
```

## 🔧 Testar Funcionalidades

### Teste 1: Cadastro de Novo Usuário

1. Acesse: `https://comex-4.onrender.com/login`
2. Clique na aba **"Cadastro"**
3. Preencha os dados
4. Clique em **"Cadastrar"**
5. **Verifique os logs** do backend para ver a notificação

### Teste 2: Redefinição de Senha

1. Na tela de login, clique em **"Redefinir Senha"**
2. Digite o email
3. **Verifique os logs** do backend para ver o token

### Teste 3: Aprovação

1. Liste cadastros pendentes: `GET /cadastros-pendentes`
2. Copie o token
3. Aprove: `POST /aprovar-cadastro` com o token
4. **Verifique os logs** para confirmação

## 📧 Configurar Email Real (Futuro)

Para enviar emails reais, você precisaria:

1. **Configurar SMTP** no `backend/services/email_service.py`
2. **Adicionar variáveis de ambiente:**
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
3. **Descomentar o código** de envio real no arquivo

## ✅ Checklist de Funcionalidades

- [ ] Cadastro de usuário funciona
- [ ] Notificação aparece nos logs do backend
- [ ] Token de aprovação gerado
- [ ] Aprovação funciona via endpoint
- [ ] Redefinição de senha funciona
- [ ] Token de redefinição aparece nos logs

## 🎯 Resumo

- **Emails não são enviados**: Apenas logados no backend
- **Ver notificações**: Acesse os logs do Render
- **Aprovar cadastros**: Use o endpoint `/aprovar-cadastro`
- **Criar usuários**: Use `/criar-usuario-teste` para usuários já aprovados

---

**Última atualização**: 05/01/2026

