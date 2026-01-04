# ✅ Tabelas Recriadas - Próximos Passos

## ✅ O que foi feito:
- Tabelas `usuarios` e `aprovacoes_cadastro` foram deletadas
- Tabelas foram recriadas com todas as colunas corretas
- Estrutura do banco está atualizada

## 🚀 Próximos Passos:

### 1. Reiniciar o Backend

Execute:
```bash
INICIAR_BACKEND_FACIL.bat
```

Aguarde aparecer:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Testar o Backend

Abra no navegador:
```
http://localhost:8000/health
```

Deve retornar:
```json
{"status": "ok"}
```

### 3. Testar o Cadastro

1. Abra o frontend: `http://localhost:3000` (ou a porta que você está usando)
2. Vá para a aba "Cadastro"
3. Preencha os dados:
   - Nome completo
   - Email
   - Senha (deve conter letras E números, ex: `senha123`)
   - Data de nascimento (opcional)
   - Nome da empresa (opcional)
   - CPF ou CNPJ
4. Clique em "Cadastrar"

### 4. Verificar se Funcionou

**Se funcionou:**
- Você verá a mensagem: "Cadastro realizado com sucesso!"
- O formulário será limpo
- A aba mudará para "Login"

**Se não funcionou:**
- Abra o Console do Navegador (F12)
- Veja os erros em vermelho
- Verifique os logs do backend

## 📧 Sobre o Email de Aprovação

O email será enviado em background. Se não chegar:

1. **Verifique os logs do backend** - você verá:
   - `✅ Email de aprovação enviado` (se funcionou)
   - `⚠️ Email não foi enviado` + link de aprovação (se não funcionou)
   - `📧 Link de aprovação: [link]` (sempre aparece nos logs)

2. **O link de aprovação também aparece nos logs**, mesmo se o email não for enviado.

3. **Para configurar o email**, crie o arquivo `backend/.env`:
   ```env
   EMAIL_SENDER=nataliadejesus2@gmail.com
   EMAIL_SENDER_PASSWORD=sua_senha_de_app
   EMAIL_ADMIN=nataliadejesus2@gmail.com
   APP_URL=http://localhost:3000
   ```

## 🔍 Troubleshooting

### Erro: "Coluna não existe"
- Execute `RECRIAR_LOGIN.bat` novamente

### Erro: "Backend não está rodando"
- Execute `INICIAR_BACKEND_FACIL.bat`

### Erro: "Email já cadastrado"
- Use outro email ou delete o usuário do banco

### Erro: "Senha inválida"
- A senha deve conter letras E números (ex: `senha123`)

---

**Última atualização**: Janeiro 2025


