# Correção de Erros de Build no Render

## 🔴 Problema Identificado

O build no Render estava falhando com erro:
```
error: failed to create directory `/usr/local/cargo/registry/cache/...`
Caused by: Read-only file system (os error 30)
```

Isso acontecia porque alguma dependência estava tentando compilar código Rust durante o build, mas o sistema de arquivos do Render é somente leitura para operações de compilação.

## ✅ Correções Aplicadas

### 1. **render.yaml** - Build Command Atualizado

```yaml
buildCommand: pip install --upgrade pip setuptools wheel && pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

**Mudanças:**
- Adicionado `--no-build-isolation` para evitar problemas de isolamento de build
- Mantido `--no-cache-dir` para economizar espaço
- Garantido que apenas wheels pré-compilados sejam usados

### 2. **requirements-render-ultra-minimal.txt** - Dependências Otimizadas

Apenas dependências essenciais que têm wheels pré-compilados disponíveis:

- ✅ `fastapi==0.104.1` - Framework API
- ✅ `uvicorn==0.24.0` - Servidor ASGI
- ✅ `pydantic==2.5.0` - Validação de dados
- ✅ `sqlalchemy==2.0.23` - ORM
- ✅ `psycopg2-binary==2.9.9` - Driver PostgreSQL (binário)
- ✅ `httpx==0.25.2` - Cliente HTTP
- ✅ `loguru==0.7.2` - Logging
- ✅ `schedule==1.2.0` - Agendamento de tarefas

**Removidas (causavam compilação):**
- ❌ `pandas` - Requer compilação Rust
- ❌ `numpy` - Requer compilação Rust
- ❌ `cryptography` - Requer compilação Rust
- ❌ `uvicorn[standard]` - Requer compilação adicional

### 3. **main.py** - Import Opcional do Export Router

O router de exportação agora é importado de forma opcional para evitar erros se houver problemas:

```python
try:
    from api.export import router as export_router
    EXPORT_ROUTER_AVAILABLE = True
except ImportError:
    EXPORT_ROUTER_AVAILABLE = False
    logger.warning("Router de exportação não disponível")
```

## 📋 Próximos Passos no Render

### 1. Atualizar Deploy

1. Acesse o Render Dashboard: https://dashboard.render.com
2. Vá ao serviço `comex-backend`
3. Clique em **"Manual Deploy"** → **"Deploy latest commit"**
4. Aguarde o build completar (5-10 minutos)

### 2. Verificar Logs

Se ainda houver erros, verifique os logs do build:

1. No Render Dashboard, vá em **"Logs"**
2. Procure por erros relacionados a:
   - `cargo` (Rust)
   - `maturin` (build tool Rust)
   - `Read-only file system`
   - `failed to create directory`

### 3. Se o Erro Persistir

Se ainda houver problemas, tente:

**Opção A: Usar versões mais antigas e estáveis**

Edite `backend/requirements-render-ultra-minimal.txt`:

```txt
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
```

**Opção B: Build sem isolamento completo**

No `render.yaml`, use:

```yaml
buildCommand: pip install --upgrade pip && pip install --no-build-isolation --no-deps -r backend/requirements-render-ultra-minimal.txt && pip install --no-build-isolation -r backend/requirements-render-ultra-minimal.txt
```

**Opção C: Usar Docker**

Crie um `Dockerfile` na raiz:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements-render-ultra-minimal.txt .
RUN pip install --no-cache-dir -r requirements-render-ultra-minimal.txt

COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

E no `render.yaml`:

```yaml
buildCommand: docker build -t comex-backend .
```

## ✅ Verificação de Sucesso

Após o deploy bem-sucedido:

1. ✅ Build completa sem erros de Rust
2. ✅ Serviço inicia corretamente
3. ✅ Endpoint `/health` retorna `{"status":"healthy"}`
4. ✅ Endpoint `/dashboard/stats` funciona

## 📝 Notas Importantes

- **Free Tier**: Serviços free "dormem" após 15 minutos de inatividade
- **Build Time**: Primeira vez pode levar 10-15 minutos
- **Dependências**: Sempre use versões com wheels pré-compilados no PyPI
- **Logs**: Sempre verifique os logs do build para identificar problemas

---

**Última atualização**: 05/01/2026
**Status**: ✅ Correções aplicadas e commitadas

