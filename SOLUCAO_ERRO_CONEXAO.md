# 🔧 Solução: Erro de Conexão com Backend

## ⚠️ Erro Reportado
"Não foi possível conectar ao servidor. Verifique se o backend está rodando em http://localhost:8000"

## 🔍 Causa
O frontend não consegue se conectar ao backend porque o backend não está rodando.

## ✅ Solução Rápida

### 1. Verificar se o Backend está Rodando

Execute:
```bash
VERIFICAR_BACKEND.bat
```

Ou teste manualmente:
```bash
curl http://localhost:8000/health
```

### 2. Iniciar o Backend

**Opção A - Script Automático (Recomendado):**
```bash
REINICIAR_BACKEND.bat
```

**Opção B - Manual:**
```bash
cd backend
python run.py
```

**Opção C - Com uvicorn direto:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verificar se Funcionou

Após iniciar o backend, você deve ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4. Testar Conexão

Abra no navegador:
```
http://localhost:8000/health
```

Deve retornar:
```json
{"status": "ok"}
```

### 5. Tentar Cadastrar Novamente

Agora volte para a tela de cadastro e tente novamente.

## 🔍 Verificações Adicionais

### Verificar Porta 8000

Se a porta 8000 estiver ocupada:

1. **Windows PowerShell:**
```powershell
netstat -ano | findstr :8000
```

2. **Matar processo (se necessário):**
```powershell
taskkill /PID [NUMERO_DO_PID] /F
```

### Verificar Firewall

Certifique-se de que o firewall não está bloqueando a porta 8000.

### Verificar Variáveis de Ambiente

Se o frontend está em outra porta (ex: 3004), verifique se há arquivo `.env` no frontend:

```env
REACT_APP_API_URL=http://localhost:8000
```

## 📋 Checklist

- [ ] Backend está rodando (verifique a janela do PowerShell)
- [ ] Porta 8000 está livre
- [ ] `http://localhost:8000/health` retorna `{"status": "ok"}`
- [ ] Frontend está configurado para usar `http://localhost:8000`
- [ ] Não há erros no console do backend

## 🆘 Se Ainda Não Funcionar

1. **Verifique os logs do backend** - Veja se há erros na inicialização
2. **Verifique o console do navegador (F12)** - Veja a mensagem de erro completa
3. **Teste com curl ou Postman:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Verifique se há outro processo usando a porta:**
   ```powershell
   netstat -ano | findstr :8000
   ```

---

**Última atualização**: Janeiro 2025
