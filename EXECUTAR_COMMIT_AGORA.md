# 🚀 Executar Commit e Push Agora

## ⚡ Opção Rápida (Recomendada)

Execute um dos scripts abaixo no PowerShell ou CMD:

### Opção 1: Script Batch
```batch
.\FORCE_COMMIT.bat
```

### Opção 2: Script Python
```powershell
python executar_commit_push.py
```

### Opção 3: Comandos Manuais

Abra o PowerShell ou CMD no diretório do projeto e execute:

```powershell
cd "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex"

# 1. Adicionar todos os arquivos
git add -A

# 2. Verificar status
git status --short

# 3. Fazer commit
git commit -m "Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário" -m "- Remove senhas expostas dos arquivos .md" -m "- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)" -m "- Adiciona endpoint POST /admin/usuarios/deletar-por-email" -m "- Cria script deletar_usuarios.py para deletar usuários específicos" -m "- Corrige render.yaml removendo duplicação"

# 4. Fazer push
git push origin main
```

## 📋 Arquivos que Serão Commitados

- `backend/main.py` - Endpoint deletar usuário por email
- `frontend/src/pages/Dashboard.js` - Ajustes mobile/responsivo
- `render.yaml` - Configurações de deploy
- `backend/scripts/deletar_usuarios.py` - Script para deletar usuários
- `URL_CORRETA_DATABASE.md` - Senhas removidas
- `CORRIGIR_URL_POSTGRESQL.md` - Senhas removidas
- `RESUMO_IMPORTACAO_ATUAL.md` - Senhas removidas
- `GUIA_TESTE_PASSO_A_PASSO.md` - Senhas removidas

## ✅ Após o Push

O Render detectará automaticamente as mudanças e fará o deploy em 5-10 minutos.

Acompanhe em: https://dashboard.render.com

## 🗑️ Deletar Usuários Após Deploy

Após o deploy, execute via API:

```powershell
# Deletar daniel.borba@grupoht.com.br
curl -X POST "https://comex-backend-gecp.onrender.com/admin/usuarios/deletar-por-email?email=daniel.borba@grupoht.com.br"

# Deletar andre.rodrigues@grupoht.com.br
curl -X POST "https://comex-backend-gecp.onrender.com/admin/usuarios/deletar-por-email?email=andre.rodrigues@grupoht.com.br"
```

Ou execute o script Python:

```powershell
python backend/scripts/deletar_usuarios.py
```

---

**Se "nothing to commit" aparecer**, significa que as mudanças já foram commitadas. Nesse caso, apenas faça o push:

```powershell
git push origin main
```
