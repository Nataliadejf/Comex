# 🔧 Como Corrigir Erro de Compilação Rust no Render

## Problema

Erro ao fazer deploy:
```
error: failed to create directory `/usr/local/cargo/registry/cache/...`
Caused by: Read-only file system (os error 30)
💥 maturin failed
```

## Causa

O serviço está usando `requirements.txt` que contém:
- `pydantic==2.5.0` (requer compilação Rust)
- `pydantic-core==2.14.1` (requer Rust toolchain)
- Versões novas que precisam compilar código

## Solução

### No Render Dashboard:

1. **Acesse o serviço** (ex: "Comex-5")
2. **Vá em Settings**
3. **Encontre "Build Command"**
4. **Substitua por:**
   ```bash
   pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
   ```

5. **Verifique Python Version:**
   - Deve ser `3.11.0` (NÃO 3.13)

6. **Salve e faça Manual Deploy**

## Diferença entre os arquivos:

- ❌ `requirements.txt` - Versões novas, requerem Rust
- ✅ `requirements-render-ultra-minimal.txt` - Versões antigas, wheels pré-compilados

## Verificação

Após o deploy, verifique os logs:
- ✅ Deve mostrar: "Successfully installed fastapi-0.95.2 uvicorn-0.22.0..."
- ❌ NÃO deve mostrar: "maturin", "cargo", "Rust toolchain"
