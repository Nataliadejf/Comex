# Como Verificar o Erro Específico no Render

## 🔍 Passo a Passo para Identificar o Erro

### 1. Acessar os Logs Completos

1. No Render Dashboard, vá ao serviço `comex-backend`
2. Clique em **"Logs"** (no menu lateral esquerdo)
3. Role até o **final dos logs** para ver o erro específico
4. Procure por mensagens que começam com:
   - `Error:`
   - `Traceback:`
   - `ModuleNotFoundError:`
   - `ImportError:`
   - `AttributeError:`

### 2. Erros Comuns e Soluções

#### Erro: `ModuleNotFoundError: No module named 'httpx'`
**Solução:** O código está tentando importar httpx mas ele não está instalado.
- ✅ **Já corrigido:** O código agora usa `aiohttp` como fallback
- Se ainda aparecer, verifique se o commit `6d3127d` está sendo usado

#### Erro: `ModuleNotFoundError: No module named 'aiohttp'`
**Solução:** O `aiohttp` não foi instalado corretamente.
- Verifique se `requirements-render-ultra-minimal.txt` contém `aiohttp==3.8.5`
- Verifique se o build completou com sucesso

#### Erro: `sqlalchemy.exc.OperationalError` ou `database locked`
**Solução:** Problema com o banco de dados.
- Verifique se `DATABASE_URL` está configurada corretamente no Render
- Se estiver usando SQLite, pode haver problema de permissões

#### Erro: `AttributeError: 'Settings' object has no attribute '...'`
**Solução:** Problema com configurações do Pydantic v1.
- Verifique se o `config.py` tem o fallback correto para Pydantic v1

#### Erro: `ImportError: cannot import name 'BaseSettings' from 'pydantic'`
**Solução:** Problema com Pydantic v1.
- ✅ **Já corrigido:** O `config.py` agora tem fallback para Pydantic v1
- Se ainda aparecer, verifique se o commit está atualizado

### 3. Verificar Variáveis de Ambiente

No Render Dashboard:
1. Vá em **"Environment"** (no menu lateral)
2. Verifique se estas variáveis estão configuradas:
   - `DATABASE_URL` - **OBRIGATÓRIA**
   - `COMEX_STAT_API_URL` - Opcional (já tem valor padrão)
   - `SECRET_KEY` - Deve ser gerada automaticamente
   - `ENVIRONMENT=production`
   - `DEBUG=false`

### 4. Verificar o Build

1. Vá em **"Events"** (no menu lateral)
2. Clique no deploy mais recente
3. Verifique se o build completou com sucesso:
   - ✅ Deve mostrar "Build succeeded"
   - ✅ Deve mostrar "Successfully installed" com todas as dependências

### 5. Testar o Health Check

Após o deploy, teste o endpoint de health:
```
https://seu-backend.onrender.com/health
```

Deve retornar:
```json
{"status":"healthy","database":"connected"}
```

Se retornar erro, copie a mensagem de erro completa.

## 📋 Checklist de Verificação

- [ ] Build completou com sucesso
- [ ] Todas as dependências foram instaladas
- [ ] Variável `DATABASE_URL` está configurada
- [ ] Logs não mostram erros de importação
- [ ] Endpoint `/health` responde corretamente

## 🐛 Se o Erro Persistir

1. **Copie o erro completo** dos logs (últimas 50-100 linhas)
2. **Verifique o commit** que está sendo usado no deploy
3. **Confirme** que todas as alterações foram commitadas e enviadas para o GitHub

## 📝 Próximos Passos

Após identificar o erro específico:
1. Compartilhe a mensagem de erro completa
2. Verifique qual linha do código está causando o problema
3. Aplique a correção necessária
4. Faça commit e push
5. Faça novo deploy no Render

---

**Última atualização**: 05/01/2026
**Commit atual**: `6d3127d`

