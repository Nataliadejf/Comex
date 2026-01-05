# ✅ Checklist Pós-Deploy

## 🎯 Passos Imediatos

### 1️⃣ Copiar URL do Serviço
- [ ] No Render Dashboard, vá para o serviço "Comex"
- [ ] Copie a URL (exemplo: `https://comex-xxxxx.onrender.com`)
- [ ] Guarde essa URL!

### 2️⃣ Testar Health Check
- [ ] Acesse: `https://[SUA-URL]/health`
- [ ] Deve retornar: `{"status": "healthy", "database": "connected"}`
- [ ] Se retornar erro, verifique `DATABASE_URL` nas variáveis de ambiente

### 3️⃣ Verificar Banco de Dados
- [ ] Render Dashboard → Serviço "Comex" → "Environment"
- [ ] Verifique se `DATABASE_URL` está configurada
- [ ] Se não estiver:
  - [ ] Criar PostgreSQL no Render
  - [ ] Copiar "Internal Database URL"
  - [ ] Colar em `DATABASE_URL`
  - [ ] Salvar e aguardar redeploy

### 4️⃣ Testar Endpoints
- [ ] Teste: `https://[SUA-URL]/`
- [ ] Teste: `https://[SUA-URL]/health`
- [ ] Teste: `https://[SUA-URL]/dashboard/stats?meses=3`

### 5️⃣ Configurar Frontend
- [ ] Edite `frontend/.env` (ou crie se não existir)
- [ ] Adicione: `REACT_APP_API_URL=https://[SUA-URL-DO-RENDER]`
- [ ] Reinicie o frontend: `npm start`

## 🎉 Pronto para Usar!

Após completar esses passos, sua aplicação estará funcionando!

