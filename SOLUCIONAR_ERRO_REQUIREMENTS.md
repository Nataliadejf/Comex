# 🔧 Solucionar Erro: requirements-render-ultra-minimal.txt não encontrado

## 🔍 Problema Identificado

**Erro:**
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'backend/requirements-render-ultra-minimal.txt'
```

**Causa:**
O Root Directory está configurado como `backend`, mas o Build Command está tentando acessar `backend/requirements-render-ultra-minimal.txt`.

**Explicação:**
- Se Root Directory = `backend`, o caminho relativo é `requirements-render-ultra-minimal.txt` (sem `backend/`)
- Se Root Directory = `.` (raiz), o caminho relativo é `backend/requirements-render-ultra-minimal.txt` (com `backend/`)

---

## ✅ Solução 1: Corrigir Root Directory (RECOMENDADO)

**No Render Dashboard:**

1. **Vá em:** comex-backend → Settings → Build & Deploy
2. **Root Directory:**
   - Clique em **"Edit"**
   - Altere de `backend` para `.` (ponto - raiz do projeto)
   - Clique em **"Save"**

3. **Build Command** (já está correto):
   ```bash
   pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
   ```

4. **Start Command** (já está correto):
   ```bash
   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
   ```

---

## ✅ Solução 2: Ajustar Build Command (Alternativa)

Se preferir manter Root Directory = `backend`, ajuste o Build Command:

**Build Command alternativo:**
```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r requirements-render-ultra-minimal.txt
```

**Diferença:** Remove `backend/` do caminho porque já está dentro do diretório `backend`.

---

## 📋 Configuração Recomendada (Solução 1)

### Build & Deploy:
- **Root Directory:** `.` (raiz do projeto) ⚠️ **CORRIGIR**
- **Build Command:** (manter como está)
- **Start Command:** (manter como está)

### Por que usar Root Directory = `.`?
- ✅ Permite acesso a arquivos na raiz do projeto
- ✅ Build Command pode usar `backend/requirements-render-ultra-minimal.txt`
- ✅ Start Command pode usar `cd backend && ...`
- ✅ Mais flexível para futuras mudanças

---

## 🔍 Verificar Arquivo no Git

Certifique-se que o arquivo está commitado:

```bash
# Verificar se está no Git
git ls-files backend/requirements-render-ultra-minimal.txt

# Se não estiver, adicionar:
git add backend/requirements-render-ultra-minimal.txt
git commit -m "fix: Adicionar requirements-render-ultra-minimal.txt"
git push origin main
```

---

## ✅ Checklist de Correção

- [ ] Root Directory alterado para `.` (raiz)
- [ ] Build Command verificado (deve ter `backend/requirements-render-ultra-minimal.txt`)
- [ ] Start Command verificado (deve ter `cd backend && ...`)
- [ ] Arquivo `requirements-render-ultra-minimal.txt` existe em `backend/`
- [ ] Arquivo está commitado no Git
- [ ] Manual Deploy feito após correções

---

## 🚀 Após Corrigir

1. **Salve todas as alterações** no Render Dashboard
2. **Vá em "Manual Deploy"** → **"Deploy latest commit"**
3. **Aguarde o build completar**
4. **Verifique os logs** - não deve mais aparecer o erro

---

## 💡 Nota Importante

**A Solução 1 (Root Directory = `.`) é RECOMENDADA** porque:
- É mais consistente com o `render.yaml`
- Permite mais flexibilidade
- É o padrão para projetos monorepo
