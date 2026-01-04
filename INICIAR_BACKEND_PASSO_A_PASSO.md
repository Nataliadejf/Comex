# 🚀 Como Iniciar o Backend - Passo a Passo

## ⚠️ ERRO ATUAL
"Não foi possível conectar ao servidor em http://localhost:8000"

**Causa:** O backend não está rodando.

## ✅ SOLUÇÃO - 3 PASSOS SIMPLES

### PASSO 1: Abrir PowerShell na pasta do projeto

1. Abra o **Explorador de Arquivos**
2. Navegue até: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex`
3. Clique com o botão direito na pasta
4. Selecione: **"Abrir no Terminal"** ou **"Abrir no PowerShell"**

### PASSO 2: Executar o script de inicialização

**Opção A - Script Automático (Mais Fácil):**
```
REINICIAR_BACKEND.bat
```

**Opção B - Manual:**
```powershell
cd backend
python run.py
```

**Opção C - Se não funcionar:**
```powershell
cd backend
.\venv\Scripts\activate
python run.py
```

### PASSO 3: Verificar se está funcionando

Você deve ver algo assim:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## ✅ TESTE RÁPIDO

Abra no navegador:
```
http://localhost:8000/health
```

Deve retornar:
```json
{"status": "ok"}
```

## 🔄 AGORA TENTE CADASTRAR

1. Volte para a tela de cadastro no navegador
2. Preencha os dados novamente
3. Clique em "Cadastrar"
4. Deve funcionar! ✅

## ⚠️ IMPORTANTE

- **MANTENHA** a janela do PowerShell aberta enquanto usar a aplicação
- **NÃO FECHE** a janela do PowerShell (isso fecha o backend)
- Se fechar, execute `REINICIAR_BACKEND.bat` novamente

## 🆘 SE AINDA NÃO FUNCIONAR

### Verificar se Python está instalado:
```powershell
python --version
```

### Verificar se as dependências estão instaladas:
```powershell
cd backend
pip install -r requirements.txt
```

### Verificar se a porta 8000 está livre:
```powershell
netstat -ano | findstr :8000
```

Se aparecer algo, a porta está ocupada. Mate o processo ou use outra porta.

---

**Última atualização**: Janeiro 2025


