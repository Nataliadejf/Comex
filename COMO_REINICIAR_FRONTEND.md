# 🔄 Como Reiniciar o Frontend

## ⚠️ Por que precisa reiniciar?

Quando você altera o arquivo `.env`, o React **não detecta automaticamente** as mudanças. É necessário reiniciar o servidor de desenvolvimento.

## 🚀 Métodos para Reiniciar

### Método 1: Usar o Script (Mais Fácil) ✅

1. **Feche o terminal** onde o frontend está rodando (se estiver rodando)
2. **Clique duas vezes** no arquivo: `REINICIAR_FRONTEND.bat`
3. O script irá:
   - Parar processos do Node
   - Verificar o arquivo `.env`
   - Iniciar o frontend novamente
4. Aguarde alguns segundos
5. Acesse: `http://localhost:3000`

### Método 2: Manualmente

1. **Feche o terminal** onde o frontend está rodando
   - Pressione `Ctrl+C` no terminal
   - Ou feche a janela do terminal

2. **Abra um novo terminal** (PowerShell ou CMD)

3. **Navegue até a pasta do frontend:**
   ```bash
   cd projeto_comex\frontend
   ```

4. **Inicie o servidor:**
   ```bash
   npm start
   ```

5. **Aguarde** alguns segundos para o servidor iniciar

6. **Acesse:** `http://localhost:3000`

## ✅ Como Saber se Está Funcionando?

Após reiniciar, você deve ver:
- ✅ O servidor iniciando no terminal
- ✅ Mensagem: "Compiled successfully!"
- ✅ Browser abrindo automaticamente em `http://localhost:3000`
- ✅ Dashboard carregando dados (sem erro)

## 🐛 Se Ainda Der Erro

1. **Verifique o arquivo `.env`:**
   ```bash
   cd frontend
   type .env
   ```
   Deve mostrar: `REACT_APP_API_URL=https://comex-tsba.onrender.com`

2. **Limpe o cache do npm:**
   ```bash
   cd frontend
   npm cache clean --force
   ```

3. **Reinstale as dependências:**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Verifique o console do navegador:**
   - Pressione `F12` no navegador
   - Vá para a aba "Console"
   - Veja se há erros específicos

## 📝 Notas Importantes

- ⚠️ **Sempre reinicie** após alterar `.env`
- ⚠️ **Feche completamente** o terminal antes de reiniciar
- ✅ O arquivo `.env` já está configurado corretamente
- ✅ A URL da API está: `https://comex-tsba.onrender.com`

## 🎯 Resumo Rápido

```bash
# Opção 1: Script
REINICIAR_FRONTEND.bat

# Opção 2: Manual
cd frontend
npm start
```

