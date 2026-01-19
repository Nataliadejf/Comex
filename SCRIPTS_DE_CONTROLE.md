# 🚀 Scripts de Controle - Comex Analyzer

Scripts para facilitar o gerenciamento do projeto.

## 📋 Scripts Disponíveis

### 1. `REINICIAR_TUDO.bat` ⭐ (Recomendado)
**Reinicia backend e frontend simultaneamente**

- Para todos os processos existentes
- Verifica e cria arquivos `.env` se necessário
- Inicia o backend em uma janela separada
- Inicia o frontend na janela atual
- **Uso:** Clique duas vezes no arquivo

**O que acontece:**
1. Para processos do Node e Python
2. Verifica ambiente virtual do backend
3. Verifica arquivos `.env` (backend e frontend)
4. Inicia backend em nova janela (`http://localhost:8000`)
5. Aguarda 5 segundos
6. Inicia frontend (`http://localhost:3000`)

---

### 2. `PARAR_TUDO.bat`
**Para todos os processos (backend e frontend)**

- Para processos do Node (frontend)
- Para processos do Python/Uvicorn (backend)
- **Uso:** Clique duas vezes quando quiser parar tudo

---

### 3. `INICIAR_BACKEND.bat`
**Inicia apenas o backend**

- Verifica/cria ambiente virtual
- Instala dependências se necessário
- Verifica/cria arquivo `.env`
- Inicia servidor em `http://localhost:8000`
- **Uso:** Clique duas vezes quando quiser iniciar só o backend

**Endpoints disponíveis:**
- API: `http://localhost:8000`
- Documentação: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

### 4. `INICIAR_FRONTEND.bat`
**Inicia apenas o frontend**

- Para processos do Node existentes
- Verifica/cria arquivo `.env`
- Verifica/instala dependências
- Inicia servidor em `http://localhost:3000`
- **Uso:** Clique duas vezes quando quiser iniciar só o frontend

---

### 5. `REINICIAR_FRONTEND.bat`
**Reinicia apenas o frontend**

- Para processos do Node
- Verifica arquivo `.env`
- Inicia frontend novamente
- **Uso:** Clique duas vezes quando alterar `.env` do frontend

---

## 🎯 Fluxo de Trabalho Recomendado

### Primeira vez / Setup inicial:
```bash
1. REINICIAR_TUDO.bat
   ↓
2. Aguarde backend iniciar (5 segundos)
   ↓
3. Frontend iniciará automaticamente
   ↓
4. Acesse http://localhost:3000
```

### Após fazer alterações:
```bash
# Se alterou código do backend:
INICIAR_BACKEND.bat

# Se alterou código do frontend:
INICIAR_FRONTEND.bat

# Se alterou .env do frontend:
REINICIAR_FRONTEND.bat

# Se alterou ambos ou quer reiniciar tudo:
REINICIAR_TUDO.bat
```

### Para parar tudo:
```bash
PARAR_TUDO.bat
```

---

## ⚙️ Configuração dos Arquivos .env

### Backend (`backend/.env`)
```env
DATABASE_URL=sqlite:///./comex.db
COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=true
```

### Frontend (`frontend/.env`)
```env
REACT_APP_API_URL=http://localhost:8000
```

**Para produção (Render):**
```env
REACT_APP_API_URL=https://comex-tsba.onrender.com
```

---

## 🐛 Solução de Problemas

### Backend não inicia:
1. Verifique se Python está instalado
2. Execute `INICIAR_BACKEND.bat` para ver erros detalhados
3. Verifique se o ambiente virtual foi criado (`backend/venv/`)

### Frontend não inicia:
1. Execute `INICIAR_FRONTEND.bat` para ver erros detalhados
2. Verifique se Node.js está instalado (`node --version`)
3. Verifique se as dependências estão instaladas (`frontend/node_modules/`)

### Erro de conexão:
1. Verifique se o backend está rodando (`http://localhost:8000/health`)
2. Verifique o arquivo `frontend/.env` (deve apontar para `http://localhost:8000`)
3. Reinicie ambos com `REINICIAR_TUDO.bat`

### Porta já em uso:
1. Execute `PARAR_TUDO.bat`
2. Aguarde alguns segundos
3. Execute `REINICIAR_TUDO.bat`

---

## 📝 Notas Importantes

- ⚠️ **Sempre use `PARAR_TUDO.bat` antes de fechar o terminal**
- ⚠️ **Após alterar `.env`, sempre reinicie o serviço correspondente**
- ✅ **O backend roda em uma janela separada quando usa `REINICIAR_TUDO.bat`**
- ✅ **Para parar o backend, feche a janela ou use `PARAR_TUDO.bat`**
- ✅ **Para parar o frontend, pressione `Ctrl+C` na janela ou use `PARAR_TUDO.bat`**

---

## 🎉 Resumo Rápido

| Ação | Script |
|------|--------|
| Iniciar tudo | `REINICIAR_TUDO.bat` |
| Parar tudo | `PARAR_TUDO.bat` |
| Só backend | `INICIAR_BACKEND.bat` |
| Só frontend | `INICIAR_FRONTEND.bat` |
| Reiniciar frontend | `REINICIAR_FRONTEND.bat` |

---

**Dúvidas?** Verifique os logs nas janelas do terminal para mais detalhes sobre erros.





