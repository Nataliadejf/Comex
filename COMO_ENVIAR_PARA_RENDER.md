# Como Enviar Mudanças para o Render via GitHub

## 📋 Visão Geral

O Render está configurado para fazer **deploy automático** sempre que você enviar mudanças para o GitHub. Siga os passos abaixo:

## 🚀 Passo a Passo

### Opção 1: Usar o Script Automático (Recomendado)

Execute o script batch:

```bash
ENVIAR_PARA_GITHUB.bat
```

Este script irá:
1. ✅ Adicionar todas as mudanças ao Git
2. ✅ Fazer commit com mensagem descritiva
3. ✅ Enviar para o GitHub
4. ✅ O Render fará deploy automático

### Opção 2: Manualmente via Git

#### Passo 1: Verificar Mudanças

```bash
git status
```

#### Passo 2: Adicionar Arquivos

```bash
# Adicionar arquivos específicos importantes
git add backend/main.py
git add frontend/src/pages/Dashboard.js
git add frontend/src/services/api.js
git add backend/scripts/carregar_dados_excel_dashboard.py
git add backend/scripts/gerar_empresas_recomendadas.py

# Ou adicionar todas as mudanças
git add -A
```

#### Passo 3: Fazer Commit

```bash
git commit -m "feat: Integrar empresas recomendadas e dados Excel no dashboard

- Adicionar endpoints para empresas importadoras/exportadoras recomendadas
- Integrar dados do Excel ComexStat no dashboard quando banco vazio
- Atualizar frontend para exibir empresas recomendadas nas seções corretas
- Criar scripts para processar e alimentar dashboard com dados Excel"
```

#### Passo 4: Enviar para GitHub

```bash
git push origin main
```

## ⏱️ O Que Acontece Depois

1. **GitHub recebe as mudanças** (alguns segundos)
2. **Render detecta o push** (alguns segundos)
3. **Render inicia o build** (1-2 minutos)
4. **Render faz deploy** (2-5 minutos)
5. **Serviço fica online** com as novas mudanças

**Tempo total estimado: 5-10 minutos**

## 🔍 Acompanhar o Deploy

### No Render Dashboard

1. Acesse: https://dashboard.render.com
2. Clique no serviço **"comex-backend"**
3. Vá para a aba **"Events"** ou **"Logs"**
4. Você verá:
   - `Build started` - Build iniciado
   - `Build succeeded` - Build concluído
   - `Deploy started` - Deploy iniciado
   - `Deploy succeeded` - Deploy concluído

### Verificar se Funcionou

Após o deploy, teste os novos endpoints:

```bash
# Testar health check
curl https://comex-backend-wjco.onrender.com/health

# Testar empresas importadoras
curl https://comex-backend-wjco.onrender.com/dashboard/empresas-importadoras

# Testar empresas exportadoras
curl https://comex-backend-wjco.onrender.com/dashboard/empresas-exportadoras
```

## ⚠️ Arquivos que NÃO Devem Ser Enviados

O arquivo `.gitignore` já está configurado para ignorar:

- `backend/data/*.xlsx` - Arquivos Excel grandes
- `backend/data/*.json` - Arquivos JSON gerados localmente
- `.env` - Variáveis de ambiente
- `node_modules/` - Dependências do Node
- `venv/` - Ambiente virtual Python

**IMPORTANTE:** Os arquivos em `backend/data/` são gerados localmente e não devem ser commitados. O Render irá gerar esses arquivos quando necessário.

## 🐛 Problemas Comuns

### Problema: "Permission denied"

**Solução:**
- Verifique se você tem permissão para fazer push no repositório
- Verifique suas credenciais do Git

### Problema: "Deploy failed" no Render

**Solução:**
1. Verifique os logs do Render
2. Verifique se há erros de sintaxe no código
3. Verifique se todas as dependências estão no `requirements.txt`
4. Verifique se o `render.yaml` está correto

### Problema: Mudanças não aparecem no Render

**Solução:**
1. Aguarde alguns minutos (deploy pode demorar)
2. Verifique se o commit foi feito corretamente
3. Verifique se o push foi bem-sucedido
4. Verifique os logs do Render para erros

## 📝 Boas Práticas

1. **Commits descritivos**: Use mensagens claras sobre o que foi alterado
2. **Commits pequenos**: Faça commits frequentes com mudanças relacionadas
3. **Testar localmente**: Sempre teste antes de fazer push
4. **Verificar logs**: Sempre verifique os logs do Render após deploy

## 🔗 Links Úteis

- **GitHub Repositório**: https://github.com/Nataliadjf/Comex
- **Render Dashboard**: https://dashboard.render.com
- **Backend URL**: https://comex-backend-wjco.onrender.com


