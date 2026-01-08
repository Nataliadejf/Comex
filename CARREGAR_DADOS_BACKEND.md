# 📊 Carregar Dados no Backend

## ✅ Dados Já Disponíveis

Os dados já estão preparados e serão servidos automaticamente pelo backend:

### Arquivos em `backend/data/`:

1. **`empresas_recomendadas.xlsx`**
   - Empresas recomendadas com todas as informações
   - CNPJ, Razão Social, Nome Fantasia, CNAE, Estado, Endereço
   - Valores de importação/exportação
   - Peso de participação
   - Sugestões (cliente potencial / fornecedor potencial)

2. **`resumo_dados_comexstat.json`**
   - Resumo de importações e exportações
   - Valores totais
   - Número de operações

3. **`dados_ncm_comexstat.json`**
   - Dados por NCM
   - Importações e exportações por produto

---

## 🔄 Como Funciona

O backend **já está configurado** para ler esses arquivos automaticamente:

### Endpoints Disponíveis:

1. **`/dashboard/empresas-recomendadas`**
   - Lê `backend/data/empresas_recomendadas.xlsx`
   - Retorna lista de empresas recomendadas

2. **`/dashboard/empresas-importadoras`**
   - Filtra empresas que importam
   - Ordena por volume de importação

3. **`/dashboard/empresas-exportadoras`**
   - Filtra empresas que exportam
   - Ordena por volume de exportação

4. **`/dashboard/dados-comexstat`**
   - Lê `backend/data/resumo_dados_comexstat.json`
   - Retorna resumo de importações/exportações

5. **`/dashboard/dados-ncm-comexstat`**
   - Lê `backend/data/dados_ncm_comexstat.json`
   - Retorna dados por NCM

---

## ✅ Garantir que Dados Estão no Git

Os arquivos de dados precisam estar commitados no Git para serem deployados:

```bash
# Verificar se estão commitados
git ls-files backend/data/

# Se não estiverem, adicionar:
git add backend/data/*.xlsx backend/data/*.json
git commit -m "feat: Adicionar dados de empresas recomendadas e ComexStat"
git push origin main
```

---

## 🚀 Após Deploy do Backend

Após corrigir a configuração do backend e fazer deploy:

1. **Backend estará online:** `https://comex-backend-knjm.onrender.com`
2. **Dados serão servidos automaticamente** via endpoints
3. **Frontend carregará os dados** automaticamente

---

## 🧪 Testar Endpoints

Após deploy, teste:

```bash
# Health Check
curl https://comex-backend-knjm.onrender.com/health

# Empresas Recomendadas
curl https://comex-backend-knjm.onrender.com/dashboard/empresas-recomendadas?limite=10

# Empresas Importadoras
curl https://comex-backend-knjm.onrender.com/dashboard/empresas-importadoras?limite=10

# Empresas Exportadoras
curl https://comex-backend-knjm.onrender.com/dashboard/empresas-exportadoras?limite=10

# Dados ComexStat
curl https://comex-backend-knjm.onrender.com/dashboard/dados-comexstat
```

---

## 📋 Checklist

- [ ] Arquivos de dados em `backend/data/` commitados no Git
- [ ] Backend configurado corretamente no Render
- [ ] Deploy do backend realizado
- [ ] Health check funcionando (`/health`)
- [ ] Endpoints retornando dados
- [ ] Frontend conectado ao backend correto
- [ ] Dashboard carregando dados

---

## 💡 Nota Importante

**Os dados NÃO precisam ser carregados manualmente!**

O backend lê os arquivos automaticamente quando recebe requisições. Basta garantir que:
1. ✅ Arquivos estão em `backend/data/`
2. ✅ Arquivos estão commitados no Git
3. ✅ Backend está deployado corretamente
4. ✅ Backend consegue ler os arquivos (permissões OK)

---

## 🔄 Atualizar Dados

Para atualizar os dados no futuro:

1. **Substitua os arquivos** em `backend/data/`
2. **Faça commit e push**
3. **Backend fará deploy automático**
4. **Novos dados estarão disponíveis** automaticamente
