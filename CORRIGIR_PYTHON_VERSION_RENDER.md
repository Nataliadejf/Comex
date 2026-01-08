# 🔧 Corrigir Python Version no Render Dashboard

## ⚠️ Problema Identificado

O Render está usando **Python 3.13.4** por padrão, mas as versões antigas das bibliotecas não são compatíveis.

**Erro comum:**
- SQLAlchemy 1.4.46 não existe mais (só tem 2.0+)
- Pandas precisa do NumPy instalado antes
- Versões antigas não são compatíveis com Python 3.13

---

## ✅ Solução: Forçar Python 3.11.8

### No Render Dashboard:

1. **Vá em:** comex-backend → Settings → Environment
2. **Adicione/Edite variável:**
   - **Key:** `PYTHON_VERSION`
   - **Value:** `3.11.8`
3. **Clique em "Save"**

---

## 📋 Configuração Completa

### Environment Variables no Render:

- **PYTHON_VERSION** = `3.11.8` ⚠️ **CRÍTICO**
- **DATABASE_URL** = (configure manualmente)
- **COMEX_STAT_API_URL** = `https://comexstat.mdic.gov.br`
- **COMEX_STAT_API_KEY** = (deixe vazio)
- **SECRET_KEY** = (gere automaticamente)
- **ENVIRONMENT** = `production`
- **DEBUG** = `false`

---

## ✅ Correções Aplicadas

### 1. requirements-render-ultra-minimal.txt
- ✅ SQLAlchemy: `1.4.46` → `1.4.48` (última versão estável 1.4.x)
- ✅ NumPy: Adicionado `1.24.3` (dependência obrigatória do pandas)
- ✅ passlib: `passlib==1.7.4` → `passlib[bcrypt]==1.7.4`
- ✅ Ordem: NumPy antes do Pandas (importante!)

### 2. render.yaml
- ✅ PYTHON_VERSION: `3.11.0` → `3.11.8`
- ✅ Removido envVars duplicado

---

## 🚀 Após Configurar

1. **Salve todas as alterações** no Render Dashboard
2. **Vá em "Manual Deploy"** → **"Deploy latest commit"**
3. **Aguarde o build completar**
4. **Verifique os logs** - deve usar Python 3.11.8 agora

---

## 🔍 Verificar no Log

Após fazer deploy, procure no log:

```
==> Installing Python version 3.11.8...
==> Using Python version 3.11.8
```

Se ainda mostrar `3.13.4`, a variável `PYTHON_VERSION` não foi configurada corretamente.

---

## ✅ Checklist

- [ ] Variável `PYTHON_VERSION=3.11.8` configurada no Render Dashboard
- [ ] requirements-render-ultra-minimal.txt atualizado
- [ ] render.yaml atualizado
- [ ] Commit e push realizados
- [ ] Manual Deploy feito após correções
- [ ] Log mostra Python 3.11.8 sendo usado

---

## 💡 Por que Python 3.11.8?

- ✅ Compatível com SQLAlchemy 1.4.x
- ✅ Compatível com Pydantic 1.10.7
- ✅ Compatível com Pandas 2.0.3
- ✅ Versões antigas das bibliotecas funcionam perfeitamente
- ✅ Mais estável que Python 3.13 para este projeto
