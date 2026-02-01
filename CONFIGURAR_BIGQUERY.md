# Como Configurar BigQuery

## ⚠️ Erro Atual

Se você está vendo:
```
❌ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada
```

Isso significa que a variável de ambiente não está configurada localmente.

## 📦 Instalar dependências (PowerShell)

**Não cole blocos de markdown (```) no terminal.** Use um comando por vez:

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
python -m pip install python-dotenv google-cloud-bigquery google-auth loguru --quiet
python validar_bigquery.py
```

Se o script mostrar "OPÇÕES DE SAÍDA", escolha uma das alternativas (configurar .env, usar --apenas-dou, etc.).

## 🔧 Solução: Configurar Variável de Ambiente

### Opção 1: PowerShell (Temporário - apenas nesta sessão)

```powershell
# Substitua {SEU_JSON_AQUI} pelo conteúdo do arquivo JSON de credenciais
$env:GOOGLE_APPLICATION_CREDENTIALS_JSON = '{"type":"service_account","project_id":"...","private_key":"..."}'

# Testar
python validar_bigquery.py
```

### Opção 2: Arquivo .env (Recomendado)

1. Crie ou edite o arquivo `.env` **na pasta do projeto** ou **dentro de `backend/`** (o sistema procura nos dois lugares):
   - `projeto_comex/.env` ou
   - `projeto_comex/backend/.env`

2. O JSON pode estar em **uma linha** ou em **várias linhas**; o script lê os dois formatos.

3. **Nunca faça commit do `.env` no GitHub** — ele já está no `.gitignore`. As chaves do BigQuery não devem subir para o repositório.

### Opção 3: Configurar no Render (Para produção)

No dashboard do Render:
1. Vá em **Environment** → **Environment Variables**
2. Adicione: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
3. Cole o JSON completo das credenciais

## 📋 Como Obter as Credenciais

1. Acesse: https://console.cloud.google.com/
2. Selecione o projeto: `liquid-receiver-483923-n6`
3. Vá em **IAM & Admin** → **Service Accounts**
4. Crie ou selecione uma service account
5. Vá em **Keys** → **Add Key** → **Create new key** → **JSON**
6. Baixe o arquivo JSON
7. Use o conteúdo completo do JSON como valor da variável

## ❌ Erro 403 - Permissão (bigquery.jobs.create)

Se aparecer:

```
403 Access Denied: User does not have bigquery.jobs.create permission in project liquid-receiver-483923-n6
```

A **service account** está autenticada, mas **não tem permissão para executar consultas** no BigQuery. É preciso conceder a role **BigQuery Job User** (ou **BigQuery User**):

1. Acesse: https://console.cloud.google.com/iam-admin/iam?project=liquid-receiver-483923-n6  
2. Na lista **Principais**, localize o e-mail da service account (ex: `comex-bigquery@liquid-receiver-483923-n6.iam.gserviceaccount.com`).  
3. Clique no **lápis (Editar)** ao lado dela.  
4. Clique em **+ ADICIONAR OUTRA FUNÇÃO**.  
5. Busque e selecione **BigQuery Job User** (ou **BigQuery User** para permissão mais ampla).  
6. Clique em **Salvar**.  

A propagação pode levar 1–2 minutos. Depois, rode de novo o comando de coleta.

### 403 continua mesmo após dar permissão – o que conferir

0. **Confirmar qual conta está em uso**  
   Na pasta do projeto, rode: `python verificar_conta_bigquery.py`. Anote o **client_email** e o **project_id**. No IAM você deve editar exatamente esse e-mail e nesse projeto.

1. **Projeto certo no Google Cloud**  
   No topo da página do Console, abra o seletor de projeto e confira se está em **liquid-receiver-483923-n6** (o ID do projeto, não só o nome “My First Project”). A role precisa estar nesse projeto.

2. **Mesma service account**  
   O erro 403 agora mostra o **e-mail exato** da conta em uso. Você também pode rodar `python verificar_conta_bigquery.py` na pasta do projeto para ver **client_email** e **project_id**. No IAM, a role **BigQuery Job User** (ou **BigQuery User**) deve estar nesse **mesmo** e-mail (não em outra service account).

3. **Usar a role “BigQuery User”**  
   Se já deu **BigQuery Job User** e ainda dá 403, adicione também (ou troque por) **BigQuery User** na mesma service account. **BigQuery User** inclui permissão para criar jobs e acessar dados.

4. **Aguardar e testar de novo**  
   Às vezes o IAM demora 5–10 minutos. Espere um pouco e rode de novo:
   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
   python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 5000 --integrar-banco --executar-cruzamento
   ```

5. **Remover e recolocar a role**  
   No IAM, edite a service account, remova a função **BigQuery Job User** (ou **BigQuery User**), salve, depois adicione de novo e salve. Isso pode forçar a atualização das permissões.

6. **403 mesmo com as roles corretas no IAM**  
   - **API do BigQuery:** Em **APIs e serviços** → **Biblioteca**, procure "BigQuery API" e confira se está **habilitada** para o projeto `liquid-receiver-483923-n6`.  
   - **Propagação:** Alterações no IAM podem levar 5–10 minutos. Espere e rode o script de novo.  
   - O coletor já usa o **projeto** das credenciais explicitamente ao criar o cliente BigQuery.

### 403 "permission to query table" (ler dados da tabela/dataset)

Se o erro for **"User does not have permission to query table ... Projeto_Comex.EmpresasImEx"** (ou outra tabela), a conta pode **criar jobs** mas não pode **ler os dados** do dataset. Conceda **BigQuery Data Viewer** no dataset:

1. No Console: **BigQuery** → **Explorador** (painel esquerdo).  
2. Localize o dataset **Projeto_Comex** no projeto `liquid-receiver-483923-n6`.  
3. Clique nos **três pontinhos** ao lado de **Projeto_Comex** → **Compartilhar** (ou **Gerenciar permissões do dataset**).  
4. **Adicionar principal** → cole o e-mail da service account (ex: `comex-bigquery@liquid-receiver-483923-n6.iam.gserviceaccount.com`).  
5. **Função:** **BigQuery Data Viewer** (Visualizador de dados do BigQuery).  
6. Salvar.

## 📋 Usar as CONSULTAS (não as tabelas do dataset)

O **dataset Projeto_Comex não contém as tabelas** que o coletor precisa; os dados estão nas **consultas salvas** no BigQuery (EmpresasImEx, NCMExportacao, NCMImportacao, etc.). O script **só executa o SQL dessas consultas**; não lê tabelas do dataset.

1. No BigQuery (Explorador), abra cada **consulta salva** (EmpresasImEx, NCMExportacao, NCMImportacao, ou a consulta que já une tudo).  
2. Copie o **SQL** da consulta.  
3. Edite `backend/data_collector/bigquery_queries.json` e cole cada SQL como item do array `"queries"` (ex: `"queries": [ "SELECT ...", "SELECT ..." ]`).  
   - Se você tiver **uma** consulta que já retorna empresa + NCM + valor, use só ela.  
   - Se tiver **várias** consultas, cada uma deve retornar colunas compatíveis: `empresa_nome`, `cnpj`, `ncm`, `estado`, `municipio`, `tipo_operacao`, `data_operacao`, `valor_fob`, `quantidade`, `peso_kg`.  
4. **Ou** defina a variável de ambiente `BIGQUERY_QUERIES_JSON` com um array JSON de strings SQL.  
5. Se não houver consultas configuradas, o script avisa e não coleta nada (não usa tabelas do dataset).  
6. Na SQL você pode usar `@limite`; o script passa o limite da coleta.

**Alternativa:** salve as consultas como **views** ou **tabelas** no dataset Projeto_Comex e avise para ajustarmos o script para referenciá-las.

## ✅ Testar Configuração

Após configurar, teste:

```bash
python validar_bigquery.py
```

Deve mostrar:
- ✅ Conectado ao BigQuery
- ✅ Lista de tabelas
- ✅ Contagem de registros

## 🚀 Próximos Passos

Após validar BigQuery:
1. Execute: `python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 1000`
2. Ou teste o endpoint no Render após deploy
