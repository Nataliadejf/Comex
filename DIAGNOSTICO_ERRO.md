# 🔍 Diagnóstico de Erros - Cadastro

## ⚠️ Se você está vendo um erro, por favor informe:

1. **Onde o erro aparece?**
   - [ ] No navegador (tela de cadastro)
   - [ ] No console do navegador (F12)
   - [ ] No backend (janela do PowerShell)
   - [ ] Em ambos

2. **Qual é a mensagem de erro exata?**
   - Copie e cole a mensagem completa

3. **Quando o erro acontece?**
   - [ ] Ao clicar em "Cadastrar"
   - [ ] Durante o preenchimento do formulário
   - [ ] Após enviar o formulário
   - [ ] Outro momento

## 🔧 Erros Comuns e Soluções

### Erro: "background_tasks is not defined"
**Causa**: BackgroundTasks não foi importado corretamente

**Solução**:
1. Verifique se o backend foi reiniciado após as alterações
2. Execute: `REINICIAR_BACKEND.bat`

### Erro: "Table 'usuarios' doesn't exist"
**Causa**: Tabelas não foram criadas no banco

**Solução**:
```bash
cd backend
python scripts\atualizar_tabelas_usuarios.py
```

### Erro: "Email já cadastrado"
**Causa**: Email já existe no banco

**Solução**: Use outro email ou delete o registro existente

### Erro: "Cannot connect to backend"
**Causa**: Backend não está rodando

**Solução**:
1. Execute: `REINICIAR_BACKEND.bat`
2. Aguarde aparecer: `Uvicorn running on http://0.0.0.0:8000`

### Erro: "Senha inválida"
**Causa**: Senha não contém letras e números

**Solução**: Use uma senha com letras E números (ex: `senha123`)

## 📋 Checklist de Verificação

- [ ] Backend está rodando (verifique a janela do PowerShell)
- [ ] Tabelas do banco foram criadas
- [ ] Console do navegador está aberto (F12)
- [ ] Senha contém letras E números
- [ ] Email não foi usado anteriormente
- [ ] CPF/CNPJ não foi usado anteriormente

## 🆘 Como Reportar o Erro

Por favor, forneça:

1. **Mensagem de erro completa** (copie e cole)
2. **Onde aparece** (navegador/backend/console)
3. **Passos para reproduzir** (o que você fez antes do erro)
4. **Screenshot** (se possível)

---

**Última atualização**: Janeiro 2025


