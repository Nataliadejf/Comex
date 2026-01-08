# Configuração Manual no Render Dashboard

## Serviços Python (Backend)

### Configurações Recomendadas:

**Tipo:** Web Service  
**Environment:** Python 3  
**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

**⚠️ IMPORTANTE:** Use `requirements-render-ultra-minimal.txt` (NÃO `requirements.txt`)
- O `requirements.txt` tem versões novas que precisam compilar Rust
- O `requirements-render-ultra-minimal.txt` usa versões antigas com wheels pré-compilados

**Start Command:**
```bash
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
```

**Root Directory:** `.` (raiz do projeto)

**Python Version:** `3.11.0` (NÃO use 3.13 - pode causar problemas de compilação)

### Variáveis de Ambiente:

- `DATABASE_URL` - Configure manualmente após criar PostgreSQL
- `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`
- `COMEX_STAT_API_KEY` = (deixe vazio se não tiver)
- `SECRET_KEY` - Gere automaticamente no Render
- `ENVIRONMENT` = `production`
- `DEBUG` = `false`
- `PYTHON_VERSION` = `3.11.0`

### Health Check Path:
`/health`

---

## Notas Importantes:

1. **Não use Docker** - Configure como Python Web Service
2. **Root Directory** deve ser `.` (raiz) para que o `cd backend` funcione
3. **Port** será definido automaticamente pela variável `$PORT` do Render
4. **Não use `--workers`** - Não é suportado na versão do uvicorn instalada

---

## Verificação Pós-Deploy:

Após o deploy, verifique:
- ✅ Logs não mostram erros de importação
- ✅ Endpoint `/health` responde com `{"status": "ok"}`
- ✅ Endpoint `/dashboard/stats` retorna dados (mesmo que vazio)
