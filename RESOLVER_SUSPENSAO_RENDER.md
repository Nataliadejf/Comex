# Como Resolver Suspensão da Conta no Render

## ⚠️ Situação Atual

Sua conta no Render foi suspensa por "atividade suspeita". Isso pode ter acontecido porque:

1. **Health check timeout**: O endpoint `/health` estava demorando mais de 5 segundos (banco Neon em modo sleep)
2. **Múltiplas tentativas de conexão**: Tentativas repetidas de conectar ao banco quando ele estava dormindo
3. **Detecção automática**: Sistema do Render detectou padrões incomuns

## ✅ Correção Aplicada

O endpoint `/health` foi simplificado para:
- **Sempre retornar 200 em < 1 segundo**
- **Não consultar o banco** (evita delays quando Neon está em modo sleep)
- **Evitar timeouts** que causam suspensão

## 📧 Como Entrar em Contato com o Suporte do Render

### Opção 1: Via Dashboard (Recomendado)

1. Acesse https://dashboard.render.com
2. Clique em **"Contact Support"** ou **"Help"** (geralmente no canto inferior direito ou no menu)
3. Explique a situação:
   ```
   Olá,
   
   Minha conta foi suspensa por "atividade suspeita", mas acredito que foi um falso positivo.
   
   O que aconteceu:
   - Meu serviço backend estava com health checks lentos devido ao banco Neon (free tier) entrar em modo sleep
   - Isso causou timeouts nos health checks do Render
   - Corrigi o endpoint /health para sempre retornar rapidamente sem depender do banco
   
   Posso fornecer mais detalhes se necessário. Por favor, reative minha conta.
   
   Obrigado!
   ```

### Opção 2: Via Email

Envie email para: **support@render.com**

**Assunto:** Account Suspension Appeal - False Positive

**Corpo do email:**
```
Subject: Account Suspension Appeal - False Positive

Olá equipe Render,

Minha conta foi suspensa por "atividade suspeita", mas acredito que foi um falso positivo causado por health checks lentos.

Contexto:
- Meu serviço backend (comex-backend) estava com timeouts no health check
- O banco PostgreSQL (Neon free tier) entra em modo sleep após inatividade
- Quando o Render fazia health check, o banco demorava para "acordar", causando timeout > 5s
- Isso foi interpretado como falha do serviço

Correção aplicada:
- Simplifiquei o endpoint /health para sempre retornar 200 em < 1 segundo
- Removida a dependência do banco no health check
- O serviço agora responde instantaneamente aos health checks

Commit: 4320096 (já no GitHub)

Por favor, reative minha conta. Estou disponível para fornecer mais informações se necessário.

Obrigado!
[Nome]
[Email da conta Render]
```

### Opção 3: Via Twitter/X

Se o suporte não responder rapidamente, tente:
- **@renderdotcom** no Twitter/X
- Mencione que sua conta foi suspensa e precisa de ajuda

## 🔧 Após Reativação

Quando sua conta for reativada:

1. **O Render fará deploy automático** do último commit (já inclui a correção do health check)
2. **Verifique os logs** para confirmar que o serviço está rodando
3. **Teste o endpoint /health**: `https://seu-backend.onrender.com/health`
   - Deve retornar `{"status": "healthy", "service": "comex-backend"}` rapidamente

## 📋 Checklist de Verificação

- [ ] Contato com suporte do Render enviado
- [ ] Conta reativada
- [ ] Serviço backend rodando
- [ ] Health check respondendo rapidamente
- [ ] Frontend conectando ao backend
- [ ] Dashboard funcionando

## 💡 Prevenção Futura

Para evitar suspensões futuras:

1. **Health check sempre rápido**: O `/health` não deve depender de serviços externos (banco, APIs)
2. **Monitorar logs**: Verificar se há erros recorrentes
3. **Plano adequado**: Se usar free tier, considerar upgrade para Basic se houver muitos timeouts
4. **Banco sempre ativo**: Se usar Neon free tier, considerar upgrade ou usar banco que não dorme

## 🆘 Alternativas Temporárias

Enquanto aguarda reativação:

- **Use localmente**: Backend em `localhost:8000`, Frontend em `localhost:3000`
- **Outras plataformas**: Considere Railway, Fly.io, ou Heroku como alternativa temporária
- **VPS próprio**: Se tiver, pode hospedar temporariamente

---

**Última atualização**: 2026-02-16  
**Status**: Aguardando reativação da conta pelo suporte do Render
