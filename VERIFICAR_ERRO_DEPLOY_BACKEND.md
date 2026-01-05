# Verificar Erro no Deploy do Backend

## 🔍 Como Diagnosticar o Erro

### PASSO 1: Ver Logs do Deploy

1. **No Render Dashboard:**
   - Clique no serviço `comex-backend` (que está com erro)
   - Vá em **"Logs"** (menu lateral)
   - Ou clique em **"Events"** para ver o histórico de deploys

2. **Procurar por:**
   - ❌ Mensagens de erro em vermelho
   - ⚠️ Avisos em amarelo
   - 🔍 Linhas que começam com "Error", "Failed", "Exception"

### PASSO 2: Erros Comuns e Soluções

#### Erro 1: "ModuleNotFoundError" ou "ImportError"

**Causa:** Dependência faltando no `requirements-render-ultra-minimal.txt`

**Solução:**
- Verifique se todas as dependências necessárias estão no arquivo
- Adicione as dependências faltantes

#### Erro 2: "Database connection failed"

**Causa:** `DATABASE_URL` não configurada ou incorreta

**Solução:**
- Configure `DATABASE_URL` nas variáveis de ambiente
- Use a Internal Database URL do PostgreSQL

#### Erro 3: "Build failed" ou "pip install failed"

**Causa:** Problema ao instalar dependências

**Solução:**
- Verifique se o `requirements-render-ultra-minimal.txt` existe
- Verifique se o caminho está correto: `backend/requirements-render-ultra-minimal.txt`

#### Erro 4: "Application failed to start"

**Causa:** Erro no código ou configuração

**Solução:**
- Verifique os logs de runtime
- Verifique se o `startCommand` está correto
- Verifique se o arquivo `main.py` existe em `backend/`

#### Erro 5: "FileNotFoundError" ou "Path not found"

**Causa:** Caminho incorreto no código

**Solução:**
- Verifique se os caminhos estão relativos ao `rootDir`
- Verifique se o `rootDir` está configurado como `.` (ponto)

## 🔧 Verificar Configurações

### 1. Verificar Variáveis de Ambiente

No serviço `comex-backend`:
- Vá em **"Environment"**
- Verifique se estas variáveis estão configuradas:
  - `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`
  - `COMEX_STAT_API_KEY` = (vazio)
  - `SECRET_KEY` = (gerada automaticamente)
  - `ENVIRONMENT` = `production`
  - `DEBUG` = `false`
  - `PYTHON_VERSION` = `3.11`
  - `DATABASE_URL` = (URL do PostgreSQL, se tiver)

### 2. Verificar Build Command

O `buildCommand` deve ser:
```
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

### 3. Verificar Start Command

O `startCommand` deve ser:
```
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

### 4. Verificar Root Directory

O `rootDir` deve ser:
```
. (ponto - raiz do repositório)
```

## 📋 Checklist de Diagnóstico

- [ ] Logs do deploy verificados
- [ ] Mensagem de erro identificada
- [ ] Variáveis de ambiente verificadas
- [ ] Build Command verificado
- [ ] Start Command verificado
- [ ] Root Directory verificado
- [ ] Arquivo `requirements-render-ultra-minimal.txt` existe
- [ ] Arquivo `backend/main.py` existe

## 🎯 Próximos Passos

Após identificar o erro:

1. ✅ Anote a mensagem de erro exata
2. ✅ Verifique qual das soluções acima se aplica
3. ✅ Corrija o problema
4. ✅ Faça commit e push das correções
5. ✅ Faça um novo deploy manual no Render

---

**Última atualização**: 05/01/2026

