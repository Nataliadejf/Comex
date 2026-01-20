# 🚀 Executar Commit e Deploy Agora

## ⚡ Executar

Execute um dos scripts abaixo:

### Opção 1: Script Batch (Recomendado)
```batch
.\COMMIT_E_DEPLOY.bat
```

### Opção 2: Comandos Manuais

Abra PowerShell ou CMD no diretório do projeto e execute:

```powershell
cd "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex"

# 1. Verificar status
git status --short

# 2. Adicionar todos os arquivos
git add -A

# 3. Fazer commit
git commit -m "fix: Corrige erro React #310 e melhora tratamento BigQuery" -m "React:" -m "- Move useEffect para topo do componente (regra dos hooks)" -m "- Corrige erro React #310 causado por hooks fora de ordem" -m "" -m "Frontend:" -m "- Melhora script postbuild para criar _redirects" -m "- Garante que _redirects seja criado no build" -m "" -m "Backend:" -m "- Melhora tratamento de erro BigQuery (403)" -m "- Retorna lista vazia sem quebrar aplicação" -m "- Logs detalhados para debugging"

# 4. Fazer push
git push origin main
```

## 📋 Arquivos que Serão Commitados

- `frontend/src/pages/Dashboard.js` - Corrige erro React #310
- `frontend/package.json` - Melhora script postbuild
- `backend/main.py` - Melhora tratamento BigQuery
- `COMMIT_E_DEPLOY.bat` - Script de commit
- `EXECUTAR_AGORA.md` - Este arquivo

## ✅ Após o Push

O Render detectará automaticamente as mudanças e fará o deploy em 5-10 minutos.

### Acompanhar Deploy

1. **Backend**: https://dashboard.render.com → Serviço `comex-backend-gecp`
2. **Frontend**: https://dashboard.render.com → Serviço do frontend

### Tempo Estimado

- **Backend**: 5-10 minutos
- **Frontend**: 3-5 minutos

## 🔍 Verificações Após Deploy

### 1. Frontend
- [ ] Dashboard carrega sem erro React #310
- [ ] Não há mais erro no console
- [ ] Sidebar funciona no mobile
- [ ] Rotas funcionam corretamente

### 2. Backend
- [ ] Health check retorna 200
- [ ] Endpoints `/dashboard/*` funcionam
- [ ] Logs do BigQuery mostram warnings ao invés de errors

### 3. BigQuery
- [ ] Aplicação não quebra quando BigQuery retorna 403
- [ ] Logs mostram: "⚠️ BigQuery: Sem permissão para criar jobs..."
- [ ] Sugestões de empresas retornam lista vazia (não erro)

---

**Se "nothing to commit" aparecer**, significa que as mudanças já foram commitadas. Nesse caso, apenas faça o push:

```powershell
git push origin main
```
