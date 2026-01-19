# 📋 Guia de Importação Local e Endpoints de Teste

Este guia explica como usar o script local para importar dados diretamente no banco e como usar os endpoints de teste para diagnosticar problemas.

## 🖥️ Opção 1: Importação Local (Recomendado)

### Pré-requisitos

1. **Python 3.11+ instalado**
2. **Dependências instaladas:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Variável de ambiente DATABASE_URL configurada:**
   - Crie um arquivo `.env` na raiz do projeto com:
     ```
     DATABASE_URL=postgresql://usuario:senha@host:porta/database
     ```
   - Ou configure diretamente no sistema operacional

### Como Usar o Script Local

#### 1. Importar Arquivo Excel de Comex

```bash
# Na raiz do projeto
python importar_excel_local.py "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
```

#### 2. Importar Arquivo CNAE

```bash
python importar_excel_local.py "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\cnae\CNAE.xlsx" --tipo cnae
```

### Vantagens da Importação Local

✅ **Não depende do Render** - Funciona mesmo se o servidor estiver offline  
✅ **Mais rápido** - Conexão direta com o banco  
✅ **Melhor para debug** - Logs detalhados no arquivo `importacao_local.log`  
✅ **Sem timeout** - Não há limite de 30 segundos do Render  

### Logs

O script cria um arquivo `importacao_local.log` na raiz do projeto com:
- Progresso da importação
- Erros detalhados
- Estatísticas finais

---

## 🔍 Opção 2: Endpoints de Teste e Diagnóstico

Após fazer deploy, você pode usar estes endpoints para diagnosticar problemas:

### 1. Testar Conexão com Banco (`POST /testar-upload-banco`)

**O que faz:**
- Testa conexão com PostgreSQL
- Verifica se tabela `operacoes_comex` existe
- Insere um registro de teste
- Retorna estatísticas

**Como usar:**
```bash
curl -X POST https://comex-backend-gecp.onrender.com/testar-upload-banco
```

**Resposta esperada:**
```json
{
  "success": true,
  "mensagem": "Teste de upload bem-sucedido",
  "tabela_existe": true,
  "registros_antes": 0,
  "registros_depois": 1,
  "registro_teste_inserido": true
}
```

### 2. Testar Upload Automático (`POST /testar-upload-automatico`)

**O que faz:**
- Cria um arquivo Excel de teste em memória
- Processa usando a função `processar_excel_comex_task`
- Verifica se registros foram inseridos

**Como usar:**
```bash
curl -X POST https://comex-backend-gecp.onrender.com/testar-upload-automatico
```

**Resposta esperada:**
```json
{
  "success": true,
  "mensagem": "Teste de upload automático bem-sucedido",
  "arquivo_teste_criado": true,
  "processamento_executado": true,
  "registros_inseridos": 4
}
```

### 3. Diagnóstico Completo do Sistema (`GET /diagnostico-sistema`)

**O que faz:**
- Verifica conexão com banco
- Lista todas as tabelas
- Conta registros em cada tabela
- Verifica arquivos Excel disponíveis
- Verifica variáveis de ambiente

**Como usar:**
```bash
curl -X GET https://comex-backend-gecp.onrender.com/diagnostico-sistema
```

**Resposta esperada:**
```json
{
  "timestamp": "2026-01-17T12:00:00",
  "banco_dados": {
    "conectado": true,
    "versao": "PostgreSQL 15.1",
    "tabelas": ["operacoes_comex", "cnae_hierarquia", "empresas"],
    "total_operacoes_comex": 0,
    "total_cnae": 0
  },
  "arquivos": {
    "diretorios_verificados": [...],
    "arquivos_excel_encontrados": [...],
    "total_arquivos": 0
  },
  "ambiente": {
    "DATABASE_URL_configurado": true,
    "PYTHON_VERSION": "3.11",
    "ENVIRONMENT": "production"
  }
}
```

---

## 🚀 Fluxo Recomendado

### Passo 1: Testar Conexão
```bash
curl -X POST https://comex-backend-gecp.onrender.com/testar-upload-banco
```

Se retornar erro, verifique:
- ✅ `DATABASE_URL` está configurada corretamente no Render?
- ✅ PostgreSQL está rodando?
- ✅ Credenciais estão corretas?

### Passo 2: Importar Dados Localmente
```bash
# Importar Excel Comex
python importar_excel_local.py "caminho/para/arquivo.xlsx" --tipo comex

# Importar CNAE
python importar_excel_local.py "caminho/para/CNAE.xlsx" --tipo cnae
```

### Passo 3: Verificar Dados
```bash
curl -X GET https://comex-backend-gecp.onrender.com/diagnostico-sistema
```

Verifique se `total_operacoes_comex` e `total_cnae` aumentaram.

### Passo 4: Testar Upload Automático
```bash
curl -X POST https://comex-backend-gecp.onrender.com/testar-upload-automatico
```

Se funcionar, significa que o processamento em background está OK.

---

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
- Verifique o caminho do arquivo
- Use caminhos absolutos no Windows: `C:\Users\User\...`

### Erro: "DATABASE_URL não configurada"
- Crie arquivo `.env` na raiz do projeto
- Ou configure variável de ambiente do sistema

### Erro: "Connection refused"
- Verifique se PostgreSQL está rodando
- Verifique se `DATABASE_URL` está correta
- Teste conexão com `psql` ou cliente PostgreSQL

### Erro: "Table does not exist"
- Execute migrations primeiro:
  ```bash
  cd backend
  alembic upgrade head
  ```

### Erro 502/503 no Render
- Use importação local (Opção 1)
- Ou aguarde alguns minutos e tente novamente
- Verifique logs do Render para mais detalhes

---

## 📝 Notas Importantes

1. **Script Local é Mais Confiável**
   - Não depende de timeout do Render
   - Logs mais detalhados
   - Melhor para arquivos grandes

2. **Endpoints de Teste São Úteis Para:**
   - Diagnosticar problemas de conexão
   - Verificar se processamento funciona
   - Validar configuração do ambiente

3. **Após Importação Local:**
   - Dados estarão no banco PostgreSQL do Render
   - Dashboard deve mostrar os dados
   - Não precisa fazer upload novamente

---

## 🔗 Links Úteis

- [Documentação FastAPI BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Documentação SQLAlchemy Bulk Operations](https://docs.sqlalchemy.org/en/14/orm/persistence_techniques.html#bulk-operations)
- [Render Logs](https://dashboard.render.com/)
