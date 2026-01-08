# Solução para Problemas de Conexão com Render

## 🔍 Diagnóstico do Problema

Você está tentando acessar:
- **Backend no Render**: `https://comex-backend-wjco.onrender.com`
- **Frontend local**: `http://localhost:3000`

O erro `ERR_CONNECTION_REFUSED` indica que:
1. O frontend não está rodando localmente, OU
2. O backend no Render não está acessível, OU
3. A configuração da URL do backend está incorreta

## ✅ Soluções Passo a Passo

### SOLUÇÃO 1: Verificar e Corrigir Configuração do Frontend

#### Passo 1: Criar/Atualizar arquivo `.env`

Crie ou edite o arquivo `frontend/.env`:

```env
REACT_APP_API_URL=https://comex-backend-wjco.onrender.com
```

#### Passo 2: Verificar se o Backend está Online

Acesse no navegador:
```
https://comex-backend-wjco.onrender.com/health
```

**Deve retornar:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Se retornar erro:**
- O backend pode estar "dormindo" (plano free do Render)
- Aguarde 30-60 segundos e tente novamente
- Verifique os logs no Render Dashboard

#### Passo 3: Iniciar o Frontend

```bash
cd frontend
npm start
```

**IMPORTANTE:** Após alterar o `.env`, você DEVE reiniciar o frontend!

### SOLUÇÃO 2: Verificar Status do Backend no Render

1. **Acesse**: https://dashboard.render.com
2. **Encontre o serviço**: `comex-backend` ou `comex-backend-wjco`
3. **Verifique**:
   - Status deve ser "Live" (verde)
   - Se estiver "Sleeping" (amarelo), clique em "Manual Deploy" → "Deploy latest commit"
   - Verifique os logs para erros

### SOLUÇÃO 3: Usar Backend Local (Alternativa)

Se o Render estiver com problemas, use backend local:

#### Passo 1: Iniciar Backend Local

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Passo 2: Configurar Frontend para Backend Local

Edite `frontend/.env`:
```env
REACT_APP_API_URL=http://localhost:8000
```

#### Passo 3: Reiniciar Frontend

```bash
cd frontend
npm start
```

### SOLUÇÃO 4: Verificar CORS (se necessário)

O backend já está configurado para aceitar requisições de qualquer origem. Se ainda houver problemas de CORS:

1. Verifique `backend/main.py` - deve ter:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🛠️ Scripts de Ajuda

Execute o script de verificação:
```bash
VERIFICAR_E_CORRIGIR_CONEXAO.bat
```

Este script irá:
- ✅ Verificar/criar arquivo `.env`
- ✅ Testar conexão com backend
- ✅ Verificar configurações
- ✅ Mostrar próximos passos

## 📋 Checklist de Troubleshooting

- [ ] Arquivo `frontend/.env` existe e tem `REACT_APP_API_URL` configurado
- [ ] Frontend foi reiniciado após alterar `.env`
- [ ] Backend está acessível em `https://comex-backend-wjco.onrender.com/health`
- [ ] Não há erros nos logs do Render
- [ ] Porta 3000 não está sendo usada por outro processo
- [ ] CORS está configurado corretamente no backend

## 🔗 URLs Importantes

- **Backend Render**: https://comex-backend-wjco.onrender.com
- **Health Check**: https://comex-backend-wjco.onrender.com/health
- **Render Dashboard**: https://dashboard.render.com
- **Frontend Local**: http://localhost:3000

## 💡 Dicas Importantes

1. **Plano Free do Render**: O serviço "dorme" após 15 minutos de inatividade. A primeira requisição pode demorar 30-60 segundos.

2. **Variáveis de Ambiente**: No React, variáveis devem começar com `REACT_APP_` e o frontend precisa ser reiniciado após alterações.

3. **Build vs Development**: Em desenvolvimento (`npm start`), o `.env` é lido automaticamente. Em produção (build), as variáveis são injetadas no build.

4. **Logs**: Sempre verifique os logs do Render para identificar problemas específicos.

## 🆘 Se Nada Funcionar

1. **Use Backend Local Temporariamente**:
   - Inicie backend local
   - Configure frontend para `http://localhost:8000`
   - Teste se funciona localmente

2. **Verifique Logs do Render**:
   - Acesse Render Dashboard → Seu Serviço → Logs
   - Procure por erros de inicialização
   - Verifique se há problemas com dependências

3. **Recrie o Serviço no Render** (último recurso):
   - Delete o serviço atual
   - Crie novo serviço usando o `render.yaml`
   - Configure variáveis de ambiente novamente


