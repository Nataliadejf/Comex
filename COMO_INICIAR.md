# 🚀 Como Iniciar o Projeto Comex Analyzer

## ✅ Status Atual

- ✅ **Backend**: Funcionando em http://localhost:8000
- ⚠️ **Frontend**: Precisa ser iniciado

## 📋 Passo a Passo

### 1️⃣ Iniciar o Backend (se não estiver rodando)

**Opção A: Script Automático (Recomendado)**
```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
.\INICIAR_BACKEND.ps1
```

**Opção B: Manual**
```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python run.py
```

✅ **Verificar**: Acesse http://localhost:8000/health

### 2️⃣ Iniciar o Frontend

**Opção A: Script Automático (Recomendado)**
```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
.\INICIAR_FRONTEND.ps1
```

**Opção B: Manual**
```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\frontend
npm install  # Primeira vez apenas
npm start
```

⏳ **Aguarde**: A compilação pode levar 1-2 minutos na primeira vez

### 3️⃣ Acessar a Aplicação

Após iniciar ambos os serviços:

- **Frontend (Interface Principal)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

## 🔍 Verificar se Está Funcionando

### Testar Backend:
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
```

Deve retornar: `{"status":"healthy","database":"connected"}`

### Testar Frontend:
Abra o navegador em: http://localhost:3000

## ⚠️ Problemas Comuns

### Erro: "Port already in use"
**Solução**: 
```powershell
# Ver processos na porta
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Matar processo (substitua PID)
taskkill /PID <PID> /F
```

### Erro: "Cannot find module"
**Solução**:
```powershell
cd frontend
npm install
```

### Erro: "Module not found" (Backend)
**Solução**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📝 Ordem de Inicialização

1. **Primeiro**: Backend (porta 8000)
2. **Segundo**: Frontend (porta 3000)
3. **Terceiro**: Acessar http://localhost:3000

## 🎯 Scripts Disponíveis

- `INICIAR_BACKEND.ps1` - Inicia o backend automaticamente
- `INICIAR_BACKEND.bat` - Versão batch para CMD
- `INICIAR_FRONTEND.ps1` - Inicia o frontend automaticamente
- `INICIAR_FRONTEND.bat` - Versão batch para CMD

## ✅ Checklist

- [ ] Backend rodando em http://localhost:8000
- [ ] Frontend rodando em http://localhost:3000
- [ ] Navegador aberto em http://localhost:3000
- [ ] Dashboard carregando corretamente

---

**Última atualização**: Janeiro 2025



