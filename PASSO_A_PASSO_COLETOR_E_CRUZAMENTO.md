# Passo a passo: Coletor de Dados Públicos e Cruzamento

Siga na ordem. O que puder ser rodado por script está no PowerShell; o restante é manual.

---

## Passo 1: Pasta do projeto

Abra o PowerShell e vá para a pasta do projeto:

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
```

---

## Passo 2: Arquivo `.env` (manual)

Crie ou edite o arquivo **`.env`** na raiz do projeto (mesma pasta do `validar_bigquery.py`).

**Nome do arquivo:** `.env`  
**Caminho:** `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\.env`

**Conteúdo mínimo (uma linha, sem quebra):**

```
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"liquid-receiver-483923-n6","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...@....iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token",...}
```

- Substitua todo o valor por **uma única linha** com o JSON completo da chave do Google Cloud (o mesmo que você colocou no Render).
- Não use aspas em volta do JSON no `.env`; apenas `NOME=valor`.
- Se tiver **DATABASE_URL** (PostgreSQL), adicione outra linha:  
  `DATABASE_URL=postgresql://usuario:senha@host:porta/banco`

---

## Passo 3: BigQuery – usar as CONSULTAS (não as tabelas do dataset)

O **dataset Projeto_Comex não contém as tabelas**; os dados estão nas **consultas salvas** no BigQuery (EmpresasImEx, NCMExportacao, NCMImportacao, etc.). O script **não lê tabelas**; ele **executa o SQL dessas consultas**. Você deve colar o SQL de cada consulta salva em `backend/data_collector/bigquery_queries.json` (ver CONFIGURAR_BIGQUERY.md, seção "Usar as CONSULTAS"). Alternativa: salvar as consultas como views/tabelas no dataset.

Referência de colunas (para montar/validar o SQL das consultas). O relacionamento é: **EmpresasImEx** (lista de empresas) × **NCMExportacao** / **NCMImportacao** (dados por NCM e UF), ligando por `sigla_uf = sigla_uf_ncm`.

**Tabela `EmpresasImEx`** (lista de empresas importadoras e exportadoras):

| Coluna                    | Uso                              |
|---------------------------|-----------------------------------|
| `ano`                     | Ano                               |
| `cnpj`                    | CNPJ (14 dígitos)                 |
| `razao_social`            | Razão social                      |
| `id_exportacao_importacao`| Tipo (importadora/exportadora)    |
| `id_municipio`            | ID do município                   |
| `id_municipio_nome`       | Nome do município                 |
| `sigla_uf`                | Sigla do estado (ex: SP)          |
| `sigla_uf_nome`           | Nome do estado                    |
| `cnae_2_primaria`, etc.   | CNAE e demais campos             |

**Tabela `NCMExportacao`** (dados por NCM e UF – sem empresa):

| Coluna                   | Uso                    |
|--------------------------|------------------------|
| `Linha`, `ano`, `mes`    | Identificação e data   |
| `id_ncm`                 | Código NCM             |
| `sigla_uf_ncm`           | UF (liga com EmpresasImEx.sigla_uf) |
| `sigla_uf_ncm_nome`      | Nome da UF             |
| `valor_fob_dolar`        | Valor FOB em USD       |
| `quantidade_estatistica` | Quantidade             |
| `peso_liquido_kg`        | Peso líquido           |
| `id_pais`, `sigla_pais_iso3`, etc. | Demais campos  |

**Tabela `NCMImportacao`** (dados por NCM e UF – sem empresa):

| Coluna                   | Uso                    |
|--------------------------|------------------------|
| `Linha`, `ano`, `mes`    | Identificação e data   |
| `id_ncm`                 | Código NCM             |
| `sigla_uf_ncm`           | UF (liga com EmpresasImEx.sigla_uf) |
| `valor_fob_dolar`        | Valor FOB em USD       |
| `quantidade_estatistica` | Quantidade             |
| `peso_liquido_kg`        | Peso líquido           |
| `valor_frete`, `valor_seguro` | Opcionais          |

**Tabelas por município** (para cruzamento por município):

- **`municipio_exportacao`**: `Linha`, `ano`, `mes`, `id_sh4`, `id_pais`, `sigla_uf`, `sigla_uf_nome`, `id_municipio`, `id_municipio_nome`, `peso_liquido_kg`, `valor_fob_dolar`
- **`municipio_importacao`**: mesmas colunas.

**Projeto e dataset:** `liquid-receiver-483923-n6.Projeto_Comex`

O coletor faz **JOIN** de `EmpresasImEx` com `NCMExportacao` e `NCMImportacao` em `sigla_uf = sigla_uf_ncm` para obter (empresa, NCM, UF, valor).

---

## Passo 4: Instalar dependências (PowerShell)

No PowerShell, na pasta do projeto:

```powershell
python -m pip install python-dotenv google-cloud-bigquery google-auth beautifulsoup4 requests pandas loguru --quiet
```

Ou tudo do backend:

```powershell
python -m pip install -r backend\requirements.txt --quiet
```

---

## Passo 5: Validar BigQuery (PowerShell)

```powershell
python validar_bigquery.py
```

**Esperado:** mensagem "Conectado ao BigQuery", lista de tabelas e contagem em NCMImportacao/NCMExportacao.  
**Se der erro de credencial:** confira o Passo 2 (`.env` e nome `GOOGLE_APPLICATION_CREDENTIALS_JSON`).

---

## Passo 6: Rodar coleta e cruzamento (PowerShell)

**Só BigQuery, limite 1000, sem integrar no banco (teste leve):**

```powershell
python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 1000 --salvar-csv
```

**Coleta BigQuery + integração no banco + cruzamento (use se tiver DATABASE_URL no .env):**

```powershell
python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 5000 --integrar-banco --executar-cruzamento --salvar-csv
```

**Coleta de todas as fontes (DOU + BigQuery) + integrar + cruzamento:**

```powershell
python coletar_dados_publicos_standalone.py --limite 5000 --integrar-banco --executar-cruzamento --salvar-csv
```

Os CSVs são gravados na pasta atual com nome no formato `empresas_publicas_AAAAMMDD_HHMMSS.csv`.

---

## Passo 7: Enviar código para o Git (manual, se quiser deploy)

```powershell
git add -A
git status
git commit -m "feat: coleta e cruzamento NCM UF"
git push origin main
```

Se der erro de push, use: `git pull origin main --rebase` e depois `git push origin main` de novo.

---

## Relacionamentos entre tabelas (sugestões import/export)

Os relacionamentos estão configurados para sugerir **importações e exportações por empresas recomendadas**:

| Tabela / fluxo | Função |
|----------------|--------|
| **operacoes_comex** | Operações de comércio exterior (NCM, UF, importador/exportador, valor FOB, etc.). |
| **Cruzamento NCM+UF** | Agrupa por NCM e UF; lista importadores e exportadores por grupo; atualiza **empresas_recomendadas**. |
| **empresas_recomendadas** | Tabela consolidada: CNPJ, nome, estado, tipo (importadora/exportadora/ambos), NCMs de importação/exportação, valores e peso. |
| **API de sugestões** | Endpoints usam **empresas_recomendadas** para retornar empresas por NCM, UF, importadoras e exportadoras. |

**Fluxo:** Coleta (BigQuery/DOU) → integração em **operacoes_comex** → **executar cruzamento** → preenchimento de **empresas_recomendadas** → sugestões na API (import/export por empresa recomendada).

---

## Dashboard e busca: apenas BigQuery/cruzamento (sem Excel)

- **Dashboard** (cards, gráficos, totais) e **busca por empresas** são alimentados **somente** por:
  - **operacoes_comex** (dados do BigQuery: NCM importação/exportação, município importação/exportação, EmpresasImEx + dados do webscraping DOU)
  - **empresas_recomendadas** (cruzamento NCM+UF que preenche a base de recomendação)
- **Não há fallback para Excel.** Se não houver dados na coleta/cruzamento, o dashboard pode retornar vazio até a execução da coleta e do cruzamento.
- A **busca por empresas** retorna resultados quando existem registros em **operacoes_comex** ou **empresas_recomendadas**, garantindo base para extração no DOU (empresas com autorização por NCM) e recomendação de importação/exportação mais assertiva.

---

## Passo 8: Testar na API (Render)

Depois do deploy:

1. **Status do coletor:**  
   `GET`  
   `https://comex-backend-gecp.onrender.com/api/coletar-dados-publicos/status`

2. **Disparar coleta (com cruzamento ao final):**  
   `POST`  
   `https://comex-backend-gecp.onrender.com/api/coletar-dados-publicos`  
   Body (JSON):  
   `{"limite_por_fonte": 5000, "integrar_banco": true, "executar_cruzamento": true}`

3. **Só cruzamento (dados já no banco):**  
   `POST`  
   `https://comex-backend-gecp.onrender.com/api/cruzamento-ncm-uf`

---

## Resumo do que você faz manualmente

1. Criar/editar o `.env` com `GOOGLE_APPLICATION_CREDENTIALS_JSON` (e `DATABASE_URL` se for integrar no banco).
2. Conferir no BigQuery se os nomes das colunas batem com a tabela acima; se não, avisar para ajustar a query.
3. Rodar os comandos do PowerShell (passos 4, 5 e 6) na pasta do projeto.
4. Fazer `git push` (passo 7) quando quiser atualizar o deploy.
5. Testar os endpoints no Render (passo 8) após o deploy.

---

## Script PowerShell único

Há também o script **`Executar_Coleta_E_Cruzamento.ps1`** na raiz do projeto. Uso:

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
.\Executar_Coleta_E_Cruzamento.ps1
```

Ou, para só validar o BigQuery:

```powershell
.\Executar_Coleta_E_Cruzamento.ps1 -ApenasValidar
```

Ou, para coleta com limite 5000 e cruzamento:

```powershell
.\Executar_Coleta_E_Cruzamento.ps1 -Limite 5000 -ExecutarCruzamento
```

---

## Próximos passos após coleta e cruzamento

Depois que a coleta e o cruzamento rodaram com sucesso (ex.: "COLETA CONCLUÍDA COM SUCESSO", "Cruzamento concluído: X grupos NCM/UF, Y registros em empresas_recomendadas"):

1. **Relacionamento**  
   Já está feito: o cruzamento preenche a tabela **empresas_recomendadas** a partir de **operacoes_comex**. O dashboard e as APIs de sugestão usam essa tabela.

2. **Commit e deploy**  
   Na pasta do projeto (`projeto_comex`):

   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
   git add -A
   git status
   git commit -m "feat: coleta BigQuery, integração e cruzamento NCM/UF para empresas recomendadas"
   git push origin main
   ```

   No Render: o deploy é automático ao dar push em `main`. Confira no painel se o backend (e o frontend, se aplicável) redeployou.

3. **Testar no dashboard**  
   Após o deploy, acesse o dashboard e confira:
   - Cards/resumo (totais de operações, **Valor provável (por empresas)** quando houver dados em empresas_recomendadas).
   - Lista de empresas recomendadas e empresas sugeridas (com **Valor provável por empresas** na tabela).
   - Endpoint direto: `GET /dashboard/empresas-recomendadas?limite=50`.

4. **Por que o dashboard no Render continua vazio após o deploy?**  
   O dashboard lê os dados do **PostgreSQL do Render**. Se você rodou a coleta só **no seu PC**, os dados ficaram no banco **local**; o banco do Render não é preenchido automaticamente. Para o dashboard na nuvem mostrar dados:

   - **Opção A – Disparar coleta pela API no Render**  
     No Render, configure as variáveis de ambiente do backend: `DATABASE_URL` (PostgreSQL do Render) e `GOOGLE_APPLICATION_CREDENTIALS_JSON` (chave do BigQuery). Depois dispare a coleta:
     ```http
     POST https://comex-backend-gecp.onrender.com/api/coletar-dados-publicos
     Content-Type: application/json

     {"limite_por_fonte": 5000, "integrar_banco": true, "executar_cruzamento": true}
     ```
     Assim a coleta roda no servidor e grava em **operacoes_comex** e **empresas_recomendadas** no PostgreSQL do Render.

   - **Opção B – Rodar o script local apontando para o banco do Render**  
     No `.env` local, use temporariamente o `DATABASE_URL` do PostgreSQL do Render (copie do painel do Render). Rode:
     ```powershell
     python coletar_dados_publicos_standalone.py --apenas-bigquery --integrar-banco --executar-cruzamento
     ```
     Os dados serão gravados no banco do Render. Depois volte o `DATABASE_URL` local se quiser.
