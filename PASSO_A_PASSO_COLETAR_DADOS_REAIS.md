# 📋 Passo a Passo: Coletar Dados Reais da API Comex Stat

## 🎯 Objetivo

Popular o dashboard com dados reais de todos os NCMs da API oficial do Comex Stat.

---

## ✅ PASSO 1: Configurar a URL da API no Render

### 1.1. Acessar o Render Dashboard
- Abra: https://dashboard.render.com
- Faça login se necessário

### 1.2. Encontrar o Serviço Backend
- No menu lateral, clique em **"Services"** ou **"Serviços"**
- Procure por **`comex-backend`** ou **`comex-backend-wjco`**
- Clique no serviço

### 1.3. Acessar Configurações de Ambiente
- No menu lateral do serviço, clique em **"Environment"** ou **"Variáveis de Ambiente"**

### 1.4. Adicionar/Verificar Variável `COMEX_STAT_API_URL`
- Procure se já existe `COMEX_STAT_API_URL`
- **Se NÃO existir:**
  - Clique em **"Add Environment Variable"** ou **"Adicionar Variável"**
  - **Key (Chave):** `COMEX_STAT_API_URL`
  - **Value (Valor):** `https://comexstat.mdic.gov.br`
  - Clique em **"Save Changes"** ou **"Salvar"**

- **Se JÁ existir:**
  - Verifique se o valor está correto
  - Se estiver vazio ou incorreto, edite e coloque: `https://comexstat.mdic.gov.br`

### 1.5. Adicionar Variável `COMEX_STAT_API_KEY` (Opcional)
- Clique em **"Add Environment Variable"**
- **Key:** `COMEX_STAT_API_KEY`
- **Value:** (deixe vazio se não tiver chave, ou adicione se tiver)
- Clique em **"Save Changes"**

### 1.6. Aguardar Reinicialização
- O Render reiniciará o serviço automaticamente
- Aguarde 1-2 minutos até o serviço ficar **"Live"** novamente

---

## ✅ PASSO 2: Verificar se a API Está Configurada

### 2.1. Verificar Logs do Backend
- No Render Dashboard → `comex-backend` → **"Logs"**
- Procure por mensagens como:
  - ✅ `API do Comex Stat acessível` → **Configurado corretamente**
  - ❌ `API do Comex Stat não configurada` → **Volte ao Passo 1**

### 2.2. Testar Endpoint (Opcional)
- Acesse: `https://comex-backend-wjco.onrender.com/docs`
- Procure por `GET /health`
- Execute → Deve retornar `{"status": "healthy"}`

---

## ✅ PASSO 3: Coletar Dados Reais

### Opção A: Via Swagger (Recomendado)

#### 3.1. Acessar Swagger
- Abra: `https://comex-backend-wjco.onrender.com/docs`

#### 3.2. Encontrar Endpoint
- Procure por: **`POST /coletar-dados-ncms`**
- Clique no endpoint para expandir

#### 3.3. Clicar em "Try it out"
- Botão no canto superior direito do endpoint

#### 3.4. Preencher Body
- Clique no campo **"Request body"**
- Cole ou digite:
  ```json
  {
    "ncms": null,
    "meses": 24,
    "tipo_operacao": null
  }
  ```

#### 3.5. Executar
- Clique em **"Execute"** (botão azul)
- Aguarde a resposta (pode demorar alguns segundos)

#### 3.6. Verificar Resposta
- Você verá algo como:
  ```json
  {
    "success": true,
    "message": "Coleta concluída: X registros",
    "stats": {
      "total_registros": X,
      "meses_processados": [...],
      "erros": []
    }
  }
  ```

### Opção B: Via JavaScript (Alternativa)

#### 3.1. Abrir Console do Navegador
- Pressione `F12` ou `Ctrl + Shift + J`
- Vá na aba **"Console"**

#### 3.2. Executar Código
- Cole o código abaixo e pressione Enter:
  ```javascript
  fetch('https://comex-backend-wjco.onrender.com/coletar-dados-ncms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ncms: null,
      meses: 24,
      tipo_operacao: null
    })
  })
  .then(r => r.json())
  .then(data => {
    console.log('✅ Coleta iniciada:', data);
    alert('Coleta iniciada! Acompanhe pelos logs do Render.');
  })
  .catch(error => {
    console.error('❌ Erro:', error);
    alert('Erro ao iniciar coleta: ' + error.message);
  });
  ```

---

## ✅ PASSO 4: Acompanhar a Coleta

### 4.1. Acessar Logs do Render
- No Render Dashboard → `comex-backend` → **"Logs"**

### 4.2. Procurar Mensagens de Progresso
- Procure por:
  - `Coletando dados gerais (todos os NCMs)...`
  - `Coletando 2024-01 - Importação...`
  - `✓ X registros salvos partação...`
  - `✓ X registros salvos para 2024-01 - Exportação`

### 4.3. Verificar Erros (se houver)
- Se aparecer `Erro ao coletar`, anote o erro
- Erros comuns:
  - `API do Comex Stat não está disponível` → Volte ao Passo 1
  - `Connection timeout` → API pode estar lenta, aguarde
  - `404 Not Found` → URL da API pode estar incorreta

### 4.4. Tempo Estimado
- **Coleta completa (24 meses, todos NCMs)**: 30-60 minutos
- **A coleta roda em background** - você pode fechar o navegador

---

## ✅ PASSO 5: Verificar se os Dados Foram Coletados

### 5.1. Aguardar Conclusão
- Aguarde a coleta terminar (veja pelos logs)
- Quando aparecer `Coleta concluída: X registros`, está pronto

### 5.2. Testar o Banco
- Acesse: `https://comex-backend-wjco.onrender.com/docs`
- Procure por `GET /test/empresas`
- Execute → Deve mostrar `total_registros` maior que 0

### 5.3. Testar o Dashboard
- Acesse: `https://comex-4.onrender.com/dashboard`
- Remova todos os filtros
- Clique em **"Buscar"**
- Os dados devem aparecer nos gráficos e tabelas

---

## ✅ PASSO 6: Usar o Dashboard

### 6.1. Acessar Dashboard
- Abra: `https://comex-4.onrender.com/dashboard`
- Faça login se necessário

### 6.2. Remover Filtros (Primeira Vez)
- Remova qualquer NCM do campo de filtro
- Deixe o período padrão (últimos 2 anos)
- Clique em **"Buscar"**

### 6.3. Verificar Dados
- Os cards devem mostrar valores maiores que zero
- Os gráficos devem mostrar dados
- A tabela deve mostrar operações

### 6.4. Usar Filtros
- Agora você pode filtrar por:
  - **Período**: Selecione datas
  - **NCM**: Digite qualquer NCM que existe nos dados
  - **Tipo de Operação**: Importação ou Exportação
  - **Empresas**: Use o autocomplete para buscar empresas

---

## ⚠️ Problemas e Soluções

### Problema: "API do Comex Stat não está disponível"

**Solução:**
1. Verifique se `COMEX_STAT_API_URL` está configurada no Render
2. Verifique se a URL está correta: `https://comexstat.mdic.gov.br`
3. Reinicie o serviço no Render

### Problema: Coleta não retorna dados

**Solução:**
1. Verifique os logs do Render para ver erros específicos
2. Verifique se a API está acessível publicamente
3. Pode ser que a API precise de autenticação - verifique a documentação oficial

### Problema: Dashboard ainda mostra zeros

**Solução:**
1. Verifique se a coleta foi concluída (veja logs)
2. Teste o banco: `GET /test/empresas`
3. Se o banco estiver vazio, execute a coleta novamente
4. Remova filtros do dashboard e busque novamente

---

## 📊 Resumo Rápido

1. ✅ **Configurar** `COMEX_STAT_API_URL` no Render
2. ✅ **Aguardar** serviço reiniciar (1-2 min)
3. ✅ **Executar** `POST /coletar-dados-ncms` com `ncms: null`
4. ✅ **Aguardar** coleta completar (30-60 min)
5. ✅ **Testar** dashboard sem filtros
6. ✅ **Usar** filtros normalmente

---

## 🎯 Próximos Passos Após Cora 2024-01 - Importação`
  - `Coletando 2024-01 - Expoleta

- ✅ Dashboard funcionando com dados reais
- ✅ Autocomplete de empresas funcionando
- ✅ Filtros funcionando corretamente
- ✅ Coleta automática diária às 02:00 (já configurada)

---

**Última atualização**: 05/01/2026



