# Como Acessar o Shell no Render

## 🔍 Onde Encontrar o Shell

### Passo a Passo:

1. **Acesse o Render Dashboard:**
   - Vá para: https://dashboard.render.com
   - Faça login

2. **Acesse o Serviço:**
   - Clique no serviço `comex-backend` (na lista de serviços)
   - Ou vá em "My project" → "Production" → clique em `comex-backend`

3. **Encontrar o Shell:**
   - No menu lateral esquerdo, procure por **"Shell"**
   - Está na seção **"MANAGE"**
   - Ícone: ⚡ (raio/lightning bolt)
   - Clique em **"Shell"**

4. **Abrir o Terminal:**
   - Um terminal será aberto na parte inferior da tela
   - Você verá um prompt como: `$` ou `#`

## 📋 Localização Visual

```
Render Dashboard
├── Left Sidebar
│   ├── Dashboard
│   ├── Events
│   ├── Logs
│   ├── Metrics
│   ├── MANAGE ← Aqui!
│   │   ├── Environment
│   │   ├── Shell ⚡ ← CLIQUE AQUI!
│   │   ├── Scaling
│   │   └── Previews
```

## 🎯 Usar o Shell

Após abrir o Shell:

1. **Navegar para o diretório:**
   ```bash
   cd backend
   ```

2. **Executar scripts:**
   ```bash
   python scripts/criar_usuario_aprovado.py
   ```

## ⚠️ Importante

- O Shell só funciona quando o serviço está **rodando**
- Se o serviço estiver parado, você precisa iniciá-lo primeiro
- O Shell abre um terminal dentro do container do serviço

---

**Última atualização**: 05/01/2026



