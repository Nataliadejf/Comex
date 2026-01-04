# 🔍 Guia de Debugging - Problema no Cadastro

## ⚠️ Problema Reportado
O cadastro não está finalizando.

## 🔧 Correções Aplicadas

1. ✅ Tratamento de erros melhorado no frontend
2. ✅ Validação de CPF/CNPJ corrigida (aceita com ou sem formatação)
3. ✅ Logs detalhados adicionados
4. ✅ Backend com tratamento de erros robusto

## 🚀 Passos para Resolver

### 1. Atualizar Tabelas do Banco

Execute este script para garantir que as tabelas estão atualizadas:

```bash
cd backend
python scripts\atualizar_tabelas_usuarios.py
```

### 2. Verificar Backend

Certifique-se de que o backend está rodando:

```bash
# Verificar se está rodando
curl http://localhost:8000/health

# Ou reiniciar
REINICIAR_BACKEND.bat
```

### 3. Abrir Console do Navegador

1. Abra o navegador
2. Pressione **F12** para abrir DevTools
3. Vá para a aba **Console**
4. Tente cadastrar novamente
5. Veja os logs que aparecem:
   - `Dados do formulário:` - mostra o que foi preenchido
   - `Payload enviado:` - mostra o que foi enviado ao backend
   - `Erro completo ao cadastrar:` - mostra o erro detalhado

### 4. Verificar Logs do Backend

Na janela do PowerShell onde o backend está rodando, você verá:
- `Tentativa de cadastro recebida: [email]`
- `Usuário criado com sucesso: [id]`
- Ou mensagens de erro detalhadas

### 5. Testar Endpoint Diretamente

Execute o script de teste:

```bash
cd backend
python scripts\testar_cadastro.py
```

## 🔍 Possíveis Problemas e Soluções

### Problema 1: "Email já cadastrado"
**Solução**: Use um email diferente ou delete o usuário do banco

### Problema 2: "CPF/CNPJ já cadastrado"
**Solução**: Use um documento diferente

### Problema 3: "Senha inválida"
**Solução**: A senha deve conter:
- No mínimo 6 caracteres
- Pelo menos uma letra
- Pelo menos um número
- Exemplo válido: `senha123`

### Problema 4: Erro de conexão
**Solução**: 
- Verifique se o backend está rodando
- Verifique a URL: `http://localhost:8000`
- Reinicie o backend

### Problema 5: Erro no banco de dados
**Solução**:
- Execute: `python scripts\atualizar_tabelas_usuarios.py`
- Reinicie o backend

## 📋 Checklist

- [ ] Backend está rodando em http://localhost:8000
- [ ] Tabelas do banco foram atualizadas
- [ ] Console do navegador está aberto (F12)
- [ ] Senha contém letras E números
- [ ] Email não foi usado anteriormente
- [ ] CPF/CNPJ não foi usado anteriormente

## 🆘 Se Nada Funcionar

1. **Copie o erro completo** do console do navegador
2. **Copie os logs** do backend
3. **Verifique** se há mensagens de erro específicas
4. **Teste** o endpoint diretamente com o script de teste

---

**Última atualização**: Janeiro 2025


