# 🔧 Corrigir URL do PostgreSQL

## ⚠️ Problema Identificado

A URL fornecida está incompleta. Falta o domínio completo após o hostname.

**URL fornecida (incompleta):**
```
postgresql://usuario:senha@dpg-xxxxx-a/comexdb
```

**URL correta (com domínio e porta):**
```
postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

## ✅ Como Obter a URL Completa

### No Render Dashboard:

1. Acesse: https://dashboard.render.com
2. Vá em **PostgreSQL** → `comex-db`
3. Clique na aba **"Connections"**
4. Procure por **"Internal Database URL"**
5. Copie a URL **COMPLETA** que deve incluir:
   - `postgresql://` ou `postgres://`
   - `usuario:senha@`
   - `hostname.oregon-postgres.render.com` (ou outro domínio)
   - `:5432` (porta)
   - `/database`

### Formato Esperado:

```
postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/database
```

## 🔍 Verificar URL no Render

A URL completa geralmente aparece assim no Render:

```
Internal Database URL:
postgres://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

**Importante:** 
- Se começar com `postgres://`, converta para `postgresql://`
- Deve ter o domínio completo (`.oregon-postgres.render.com` ou similar)
- Deve ter a porta `:5432`

## 📋 URL Corrigida para Usar

Baseado no padrão do Render, a URL completa deve ser:

```
postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

**Verifique no Render se o domínio é diferente** (pode ser `.oregon-postgres.render.com`, `.frankfurt-postgres.render.com`, etc.)
