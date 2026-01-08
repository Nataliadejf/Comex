# 🎯 Consolidar Tudo no Comex-4

## ✅ Decisão: Usar Apenas Comex-4

O **Comex-4** já está funcionando! É melhor consolidar tudo nele ao invés de criar múltiplos serviços.

## 🔍 Problema Identificado no Comex-5

1. **Python Version errada:** Está usando 3.13.4 ao invés de 3.11.0
2. **Arquivo não encontrado:** `backend/requirements-render-ultra-minimal.txt` não está sendo encontrado
3. **Root Directory pode estar errado**

## ✅ Solução: Configurar Comex-4 como Backend

### Se Comex-4 for Static (Frontend):
- Mantenha-o como está
- Crie um novo serviço Python chamado "comex-backend" ou renomeie o comex-5

### Se Comex-4 puder ser convertido para Python:

1. **No Render Dashboard, acesse Comex-4**
2. **Vá em Settings**
3. **Altere:**

   **Runtime:** Python 3 (se estiver como Static, pode não ser possível converter - melhor criar novo)

   **Build Command:**
   ```bash
   pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
   ```

   **Start Command:**
   ```bash
   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
   ```

   **Root Directory:** `.` (raiz do projeto)

   **Python Version:** `3.11.0` (CRÍTICO - não deixe usar 3.13)

4. **Salve e faça Manual Deploy**

## 🗑️ Limpeza Recomendada

**Remova os serviços que estão falhando:**
- Comex-5 (pode ser removido ou renomeado)
- Comex-3, Comex-2, Comex- (Docker - remover)
- comex-backend (se não estiver funcionando, remover e usar apenas comex-4)

## 📝 Checklist

- [ ] Verificar tipo do Comex-4 (Static ou Python?)
- [ ] Se for Static, manter e criar novo serviço Python
- [ ] Se puder converter, configurar como Python 3.11.0
- [ ] Remover serviços não utilizados
- [ ] Testar endpoints após deploy
