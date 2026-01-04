# 🚀 Como Iniciar o Backend - Guia Visual

## ⚠️ ERRO ATUAL
"Não foi possível conectar ao servidor em http://localhost:8000"

**Isso significa:** O backend não está rodando.

## ✅ SOLUÇÃO MAIS FÁCIL

### Método 1: Clique Duas Vezes (Mais Fácil)

1. Abra o **Explorador de Arquivos**
2. Navegue até: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex`
3. **Clique duas vezes** no arquivo: `INICIAR_BACKEND_FACIL.bat`
4. Aguarde aparecer: `Uvicorn running on http://0.0.0.0:8000`
5. **MANTENHA** a janela aberta
6. Volte para o navegador e tente cadastrar

### Método 2: Via PowerShell

1. Abra o **PowerShell** na pasta do projeto
2. Digite:
   ```powershell
   .\INICIAR_BACKEND_FACIL.bat
   ```
3. Aguarde o servidor iniciar
4. **MANTENHA** a janela aberta

## ✅ COMO SABER SE ESTÁ FUNCIONANDO

### Teste 1: Ver mensagem no PowerShell
Você deve ver:
```
🚀 INICIANDO SERVIDOR NA PORTA 8000...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Teste 2: Abrir no navegador
Abra: `http://localhost:8000/health`

Deve aparecer:
```json
{"status": "ok"}
```

## ⚠️ IMPORTANTE

- **MANTENHA** a janela do PowerShell/CMD aberta
- **NÃO FECHE** a janela (isso fecha o backend)
- Se fechar, execute o script novamente

## 🔍 VERIFICAR SE ESTÁ RODANDO

Execute:
```powershell
.\VERIFICAR_BACKEND.bat
```

Ou teste no navegador:
```
http://localhost:8000/health
```

## 🆘 PROBLEMAS COMUNS

### Problema 1: "Python não encontrado"
**Solução:** Instale Python de https://www.python.org/downloads/

### Problema 2: "Ambiente virtual não encontrado"
**Solução:** O script cria automaticamente. Se não funcionar:
```powershell
cd backend
python -m venv venv
```

### Problema 3: "Porta 8000 já está em uso"
**Solução:** O script tenta parar processos automaticamente. Se não funcionar:
```powershell
netstat -ano | findstr :8000
taskkill /F /PID [NUMERO_DO_PID]
```

### Problema 4: "Erro ao instalar dependências"
**Solução:**
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 📋 CHECKLIST

- [ ] Python está instalado (`python --version`)
- [ ] Script `INICIAR_BACKEND_FACIL.bat` existe
- [ ] Executei o script
- [ ] Vi a mensagem "Uvicorn running"
- [ ] Testei `http://localhost:8000/health`
- [ ] Janela do PowerShell está aberta
- [ ] Tentei cadastrar novamente

---

**Última atualização**: Janeiro 2025


