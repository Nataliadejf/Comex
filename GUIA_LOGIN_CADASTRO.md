# 🔐 Guia do Sistema de Login e Cadastro

## 📋 Funcionalidades

### ✅ Login
- Login por **email** (não mais username)
- Senha deve conter **letras e números**
- Acesso só após aprovação do cadastro

### ✅ Cadastro
- **Nome completo** (obrigatório)
- **Email** (obrigatório, usado como login)
- **Senha** (obrigatória, deve conter letras e números)
- **Data de nascimento** (opcional)
- **Nome da empresa** (opcional)
- **CPF ou CNPJ** (obrigatório, escolha um)

### ✅ Sistema de Aprovação
- Após cadastro, email é enviado para **nataliadejesus2@gmail.com**
- Link de aprovação no email
- Usuário só pode fazer login após aprovação
- Email de confirmação enviado após aprovação

---

## 🚀 Configuração

### 1. Configurar Email

Crie o arquivo `.env` na pasta `backend/`:

```env
EMAIL_SENDER=nataliadejesus2@gmail.com
EMAIL_SENDER_PASSWORD=sua_senha_de_app
EMAIL_ADMIN=nataliadejesus2@gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
APP_URL=http://localhost:3000
```

### 2. Senha de App do Gmail

Para Gmail, você precisa criar uma "Senha de App":

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "App" e "Mail"
3. Selecione "Outro (nome personalizado)" e digite "Comex Analyzer"
4. Clique em "Gerar"
5. Copie a senha gerada (16 caracteres)
6. Use essa senha em `EMAIL_SENDER_PASSWORD`

### 3. Instalar Dependências

```bash
cd backend
pip install python-jose[cryptography] passlib[bcrypt]
```

### 4. Reiniciar Backend

```bash
REINICIAR_BACKEND.bat
```

---

## 📧 Fluxo de Aprovação

1. **Usuário se cadastra** → Status: "pendente"
2. **Email enviado** para admin (nataliadejesus2@gmail.com)
3. **Admin clica no link** de aprovação
4. **Sistema aprova** → Status: "aprovado", Ativo: 1
5. **Email enviado** para usuário confirmando aprovação
6. **Usuário pode fazer login**

---

## 🔗 Endpoints

### POST `/login`
- Login usando email e senha
- Retorna token JWT

### POST `/register`
- Cadastro de novo usuário
- Retorna mensagem de sucesso

### GET `/aprovar/{token}`
- Aprova cadastro via token
- Token enviado por email

### GET `/me`
- Informações do usuário atual (requer autenticação)

---

## ⚠️ Importante

1. **Email Admin**: Configurado como `nataliadejesus2@gmail.com`
   - Pode ser alterado em `config.py` ou variável `EMAIL_ADMIN`

2. **Senha**: Deve conter letras E números
   - Mínimo 6 caracteres
   - Exemplo válido: `senha123`
   - Exemplo inválido: `senha` (sem números)

3. **Aprovação**: Usuário não pode fazer login até ser aprovado
   - Status deve ser "aprovado"
   - Campo `ativo` deve ser 1

4. **Token de Aprovação**: Válido por 7 dias
   - Após expirar, precisa criar novo cadastro

---

## 🧪 Testando

1. Acesse: `http://localhost:3000`
2. Vá para aba "Cadastro"
3. Preencha os dados
4. Verifique email em `nataliadejesus2@gmail.com`
5. Clique no link de aprovação
6. Faça login com email e senha

---

**Última atualização**: Janeiro 2025


