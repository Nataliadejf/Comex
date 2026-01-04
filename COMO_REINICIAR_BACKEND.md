# 🔄 Como Reiniciar o Backend

## Método 1: Usando o Script (Mais Fácil)

### Passo 1: Parar o Backend Atual

1. Encontre a **janela do PowerShell/CMD** onde o backend está rodando
2. Você verá algo como:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
3. Pressione **CTRL+C** nessa janela
4. Aguarde até aparecer algo como:
   ```
   KeyboardInterrupt
   ```

### Passo 2: Reiniciar o Backend

**Opção A - Clique Duas Vezes:**
1. Abra o **Explorador de Arquivos**
2. Navegue até: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex`
3. **Clique duas vezes** no arquivo: `INICIAR_BACKEND_FACIL.bat`

**Opção B - Via PowerShell:**
1. Abra o PowerShell na pasta `projeto_comex`
2. Digite:
   ```powershell
   .\INICIAR_BACKEND_FACIL.bat
   ```

### Passo 3: Verificar se Está Rodando

Você deve ver:
```
✅ Ambiente virtual ativado
🚀 INICIANDO SERVIDOR NA PORTA 8000...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Método 2: Script Automático (Recomendado)

Execute:
```bash
REINICIAR_BACKEND.bat
```

Este script:
- Para processos na porta 8000 automaticamente
- Reinicia o backend
- Não precisa parar manualmente

## Método 3: Manual (Se os scripts não funcionarem)

1. Abra o PowerShell na pasta `projeto_comex\backend`
2. Execute:
   ```powershell
   .\venv\Scripts\activate
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## ✅ Verificar se Está Funcionando

Abra no navegador:
```
http://localhost:8000/health
```

Deve retornar:
```json
{"status": "ok"}
```

## ⚠️ Importante

- **MANTENHA** a janela do PowerShell aberta enquanto usar a aplicação
- **NÃO FECHE** a janela (isso fecha o backend)
- Se fechar, execute o script novamente

---

**Última atualização**: Janeiro 2025


