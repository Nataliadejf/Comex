# Manter Serviços Funcionando no Render

## ✅ Serviços que DEVEM ser mantidos

Baseado na sua solicitação, mantenha os seguintes serviços que estão funcionando:

1. **Comex-3** - ✓ Deployed (Docker) - **MANTER**
2. **Comex-2** - ✓ Deployed (Docker) - **MANTER**

## 🗑️ Serviços que podem ser deletados

- **comex-backend** - ✗ Failed deploy (Python 3) - Se não estiver funcionando, pode deletar
- **Comex-** - ⏳ Deploying (Docker) - Deletar se não for necessário

## 🔍 Verificar qual serviço usar como backend

### Passo 1: Testar cada serviço

Teste os endpoints de cada serviço para ver qual está funcionando corretamente:

#### Teste Comex-3:
```
https://comex-3.onrender.com/health
```

#### Teste Comex-2:
```
https://comex-2.onrender.com/health
```

### Passo 2: Verificar resposta

O serviço correto deve retornar:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

Ou pelo menos:
```json
{
  "message": "Comex Analyzer API",
  "version": "1.0.0",
  "status": "online"
}
```

### Passo 3: Testar endpoint de dashboard

Teste o endpoint principal:
```
https://comex-3.onrender.com/dashboard/stats?meses=12
```

ou

```
https://comex-2.onrender.com/dashboard/stats?meses=12
```

## 🔧 Configurar Frontend para usar o serviço correto

Após identificar qual serviço está funcionando melhor:

### Opção 1: Usar Comex-3

1. Edite `frontend/.env`:
   ```
   REACT_APP_API_URL=https://comex-3.onrender.com
   ```

2. Reinicie o frontend:
   ```bash
   REINICIAR_FRONTEND.bat
   ```

### Opção 2: Usar Comex-2

1. Edite `frontend/.env`:
   ```
   REACT_APP_API_URL=https://comex-2.onrender.com
   ```

2. Reinicie o frontend:
   ```bash
   REINICIAR_FRONTEND.bat
   ```

## 📋 Checklist

- [ ] Testar `/health` em Comex-3
- [ ] Testar `/health` em Comex-2
- [ ] Testar `/dashboard/stats` em ambos
- [ ] Identificar qual está funcionando melhor
- [ ] Atualizar `frontend/.env` com a URL correta
- [ ] Reiniciar frontend
- [ ] Testar login no frontend
- [ ] Testar dashboard no frontend

## 🎯 Recomendação

Se ambos os serviços estão funcionando:

1. **Use Comex-3** como backend principal (parece estar mais estável)
2. **Mantenha Comex-2** como backup
3. **Deletar** `comex-backend` (se não estiver funcionando)
4. **Deletar** `Comex-` (se não for necessário)

## 🔄 Se precisar fazer deploy de atualizações

Se você fizer alterações no código e precisar atualizar os serviços:

1. Faça commit e push para GitHub:
   ```bash
   git add .
   git commit -m "Descrição das alterações"
   git push origin main
   ```

2. No Render Dashboard:
   - Vá no serviço (Comex-3 ou Comex-2)
   - Clique em **"Manual Deploy"**
   - Selecione **"Deploy latest commit"**
   - Aguarde o deploy completar

## 📝 Notas Importantes

- **Não delete** serviços que estão funcionando
- Mantenha pelo menos **um serviço** como backup
- Sempre teste após fazer deploy
- Verifique os logs se houver problemas

---

**Última atualização**: 05/01/2026

