# 🔍 Debug: Login e Cadastro Não Finalizam

## ⚠️ Problema
Nem o login nem o cadastro estão finalizando.

## 🔍 Como Debugar

### 1. Abrir Console do Navegador (F12)

1. Pressione **F12** no navegador
2. Vá para a aba **Console**
3. Tente fazer login ou cadastro
4. Veja os logs que aparecem

### 2. Verificar Logs do Backend

Na janela do PowerShell onde o backend está rodando, você verá:
- `Tentativa de login recebida: [email]`
- `Tentativa de cadastro recebida: [email]`
- `✅ Login bem-sucedido` ou `❌ Erro...`

### 3. Testar Endpoints Diretamente

**Teste de Login:**
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=seu@email.com&password=suasenha"
```

**Teste de Cadastro:**
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@exemplo.com","password":"senha123","nome_completo":"Teste"}'
```

## 🔍 Possíveis Causas

### 1. Backend não está rodando
**Sintoma:** Erro de conexão no console
**Solução:** Execute `INICIAR_BACKEND_FACIL.bat`

### 2. Usuário não está aprovado
**Sintoma:** Login retorna 401
**Solução:** Usuário precisa ser aprovado primeiro

### 3. Erro no banco de dados
**Sintoma:** Erro 500 no backend
**Solução:** Verifique os logs do backend

### 4. Problema de CORS
**Sintoma:** Erro de CORS no console
**Solução:** Backend já está configurado para permitir todas as origens

### 5. Timeout
**Sintoma:** Requisição demora muito
**Solução:** Verifique se o backend está respondendo

## 📋 Checklist

- [ ] Backend está rodando (`http://localhost:8000/health`)
- [ ] Console do navegador está aberto (F12)
- [ ] Vejo logs no console ao tentar login/cadastro
- [ ] Vejo logs no backend ao tentar login/cadastro
- [ ] Não há erros em vermelho no console
- [ ] Não há erros no backend

## 🆘 Informações para Reportar

Se ainda não funcionar, forneça:

1. **Logs do Console do Navegador** (F12 → Console)
2. **Logs do Backend** (janela do PowerShell)
3. **Mensagem de erro exata**
4. **Quando acontece** (ao clicar em Login/Cadastrar)

---

**Última atualização**: Janeiro 2025


