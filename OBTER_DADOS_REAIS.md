# Como Obter Dados Reais da API Comex

## 🎯 Objetivo

Popular o banco de dados com dados reais da API Comex Stat, não apenas dados de exemplo.

## 📋 Opções Disponíveis

### Opção 1: Coleta Automática Diária (Recomendado)

O sistema já está configurado para coletar dados automaticamente todos os dias às 02:00.

**Como funciona:**
- O scheduler roda automaticamente no backend
- Coleta dados dos últimos 24 meses
- Atualiza o banco de dados automaticamente

**Verificar se está funcionando:**
1. Acesse os logs do backend no Render
2. Procure por mensagens como:
   - `Agendador iniciado: coleta diária às 02:00`
   - `Coleta de dados iniciada`
   - `Registros coletados: X`

### Opção 2: Coleta Manual via Endpoint

Você pode disparar a coleta manualmente:

1. **Via Swagger:**
   - Acesse: `https://comex-backend-wjco.onrender.com/docs`
   - Procure por `POST /coletar-dados`
   - Clique em "Try it out" → "Execute"

2. **Via JavaScript:**
   ```javascript
   fetch('https://comex-backend-wjco.onrender.com/coletar-dados', {
     method: 'POST'
   })
   .then(response => response.json())
   .then(data => {
     console.log('✅ Coleta iniciada:', data);
     alert('Coleta de dados iniciada! Aguarde alguns minutos.');
   });
   ```

### Opção 3: Popular com Dados de Exemplo (Para Testes)

Se quiser dados rápidos para testes:

1. **Via Swagger:**
   - Acesse: `https://comex-backend-wjco.onrender.com/docs`
   - Procure por `POST /popular-dados-exemplo`
   - Preencha: `quantidade: 1000`, `meses: 24`
   - Execute

## ⏰ Quando Você Terá Todos os Dados?

### Dados Reais da API Comex:

- **Primeira coleta**: Pode levar 30-60 minutos (dependendo da quantidade de NCMs)
- **Coletas subsequentes**: Diárias às 02:00 (apenas novos dados)
- **Dados históricos**: Coleta dos últimos 24 meses na primeira execução

### Dados de Exemplo:

- **1000 registros**: 1-2 minutos
- **5000 registros**: 5-10 minutos
- **10000+ registros**: 10-20 minutos

## 🔧 Configurar Coleta Automática

O sistema já está configurado! Mas você pode ajustar:

### Variáveis de Ambiente no Render:

- `UPDATE_INTERVAL_Hours`: Intervalo entre coletas (padrão: 24 horas)
- `MONTHS_TO_FETCH`: Quantos meses buscar (padrão: 3, mas o código busca 24)

### Verificar Configuração:

1. No Render Dashboard, vá em `comex-backend` → "Environment"
2. Verifique se `COMEX_STAT_API_URL` está configurada
3. Verifique se `COMEX_STAT_API_KEY` está configurada (pode estar vazia)

## 📊 Monitorar Coleta

### Ver Logs da Coleta:

1. No Render Dashboard, vá em `comex-backend` → "Logs"
2. Procure por:
   - `Coleta de dados iniciada`
   - `Registros coletados: X`
   - `Coleta concluída`

### Verificar Quantidade de Dados:

1. Acesse: `https://comex-backend-wjco.onrender.com/docs`
2. Use o endpoint `GET /dashboard/stats`
3. Veja quantos registros existem

## ⚠️ Importante

- **API Comex Stat**: Pode ter limitações de rate limit
- **Primeira coleta**: Pode demorar bastante (vários NCMs)
- **Dados reais**: Dependem da disponibilidade da API externa
- **Dados de exemplo**: São gerados aleatoriamente para testes

## 🎯 Recomendação

1. **Para testes rápidos**: Use `/popular-dados-exemplo` com 1000-2000 registros
2. **Para dados reais**: Configure a coleta automática e aguarde
3. **Para produção**: Configure coletas automáticas diárias

---

**Última atualização**: 05/01/2026

