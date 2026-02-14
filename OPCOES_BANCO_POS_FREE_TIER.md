# Opções após fim do período free (banco de dados)

Seu banco (PostgreSQL no Render) saiu do ar porque o período gratuito acabou. Abaixo estão as alternativas considerando suas bases no **BigQuery** e o plano **Basic** do Render que você está vendo.

---

## ⚠️ Conectei o Neon (DATABASE_URL) e o dashboard continua vazio — o que fazer?

**Não desconecte o banco.** O dashboard retorna zero porque o **banco no Neon é novo e está vazio** (sem dados), não porque a conexão está errada.

1. **Confirme a URL do Neon**  
   A URL deve terminar com o nome do banco e, em muitos casos, com `?sslmode=require`.  
   Exemplo: `postgresql://usuario:senha@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`  
   No Render, em **Environment** → **DATABASE_URL**, use exatamente a connection string que o Neon mostra (copiar do painel do Neon).

2. **Crie as tabelas (se ainda não existirem)**  
   No primeiro deploy com o Neon, o backend roda migrations e `init_db()`, então as tabelas devem ser criadas. Se o deploy já rodou com o Neon e o dashboard abre (mesmo com zeros), a conexão e as tabelas tendem a estar OK.

3. **Popule o banco com dados**  
   O Neon começa vazio. Você precisa carregar dados em `operacoes_comex` de uma destas formas:
   - **Upload pelo Swagger:** Abra `https://SEU-BACKEND.onrender.com/docs`, procure **POST /upload-e-importar-excel**, clique em "Try it out", escolha o arquivo Excel (ex.: `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`) e envie. Aguarde a importação terminar e recarregue o dashboard.
   - **Arquivo no repositório:** Coloque o Excel em `backend/data/` com o nome configurado em `AUTO_IMPORT_EXCEL_FILENAME`. No próximo deploy o backend tenta importar automaticamente ao subir (se `AUTO_IMPORT_EXCEL_ON_START=true` e a tabela estiver vazia).
   - **Dados de exemplo (desenvolvimento):** Se tiver o script `popular_dados_exemplo.py`, rode-o apontando para o Neon (por exemplo definindo `DATABASE_URL` localmente com a URL do Neon e executando o script).

Depois que houver registros em `operacoes_comex`, o dashboard passa a mostrar valores e listas. **Não é necessário desconectar o banco**; basta garantir a URL correta e popular as tabelas.

---

## 1. Suas opções (resumo)

| Opção | Custo mensal | Esforço | Descrição |
|-------|--------------|---------|-----------|
| **A** | **$0** | Baixo | Usar PostgreSQL gratuito externo (Neon ou Supabase) + manter backend no Render (free ou Basic) |
| **B** | **$6** | Baixo | Plano Basic-256mb só para o **backend** + banco gratuito externo (Neon/Supabase) |
| **C** | **~$19–25** | Baixo | Backend Basic-1gb + PostgreSQL pago no Render (ou Neon/Supabase) |
| **D** | Futuro | Alto | Migrar leituras pesadas para BigQuery e usar menos PostgreSQL (projeto maior) |

---

## 2. Recomendações

### Opção A (recomendada para custo zero)

- **Banco:** criar um PostgreSQL **gratuito** em:
  - **[Neon](https://neon.tech)** (0.5 GB, conexão serverless) ou  
  - **[Supabase](https://supabase.com)** (500 MB).
- **Backend:** continuar no Render (free ou, se o free tiver sido descontinuado, Basic-256mb).
- **O que fazer:** criar o projeto no Neon/Supabase, pegar a **connection string** (DATABASE_URL) e configurá-la no Render (variável de ambiente `DATABASE_URL`). Não é necessário pagar pelo banco no Render.

Vantagem: volta a ter banco estável com **$0** de custo de banco; o único custo é o do serviço web no Render, se você optar por um plano pago.

---

### Se for aderir ao plano pago no Render (Basic)

A imagem que você mostrou é do plano **Basic** (Memory and CPU) do **serviço web** (backend), não do banco. O banco PostgreSQL no Render é cobrado à parte.

- **Basic-256mb ($6/mês)**  
  - 256 MB RAM, 0.1 CPU.  
  - **Dá para rodar** o backend Comex em modo “leve”, mas com pouco margem (Python + FastAPI + SQLAlchemy + cache). Qualquer pico ou importação pesada pode deixar o serviço lento ou instável.  
  - **Recomendação:** usar só se o orçamento for muito apertado e você aceitar risco de lentidão.

- **Basic-1gb ($19/mês)**  
  - 1 GB RAM, 0.5 CPU.  
  - **Recomendado** para o seu projeto: dashboard, filtros por empresa, autocomplete, importação de Excel e consultas a `operacoes_comex` com dezenas/centenas de milhares de linhas.  
  - Boa relação custo/estabilidade para “hobby” ou uso interno.

- **Basic-4gb ($75/mês)**  
  - Só vale se você tiver muito tráfego ou processamento pesado contínuo. Para o cenário atual do Comex Analyzer, costuma ser desnecessário.

**Resumo:**  
- Se for pagar **só um** plano no Render para o **backend**, o mais indicado é o **Basic-1gb ($19/mês)**.  
- Para o **banco**, o mais econômico é **não** usar PostgreSQL pago do Render e sim **Neon ou Supabase em plano gratuito**, configurando a `DATABASE_URL` no Render.

---

## 3. BigQuery x banco da aplicação (Neon / comex-db)

**Suas bases estão no BigQuery, mas o dashboard hoje não lê direto do BigQuery.** O fluxo é este:

| Onde estão os dados | Quem usa | Como chega no app |
|---------------------|----------|--------------------|
| **BigQuery** (Google Cloud) | Scripts de coleta | Scripts gravam no banco da aplicação (PostgreSQL/Neon). |
| **Banco da aplicação** (Neon ou comex-db) | **Backend e dashboard** | O backend só lê esse banco; o dashboard chama a API que consulta esse banco. |

- **BigQuery** = fonte dos dados (estabelecimentos → tabela `Empresa`).
- **Banco da aplicação** (Neon) = onde o backend lê para o dashboard. Sem ele populado, o dashboard fica vazio.

O **comex-db** (Suspended by Render) era esse banco. Você **não precisa** reativá-lo: use só o **Neon** em `DATABASE_URL`. Para ter dados no dashboard: (1) manter Neon em `DATABASE_URL`; (2) popular o Neon rodando o script que lê BigQuery e grava em `empresas` (ex.: `coletar_empresas_base_dos_dados.py` com `DATABASE_URL`=Neon); (3) para `operacoes_comex`, usar upload de Excel (Swagger) ou dados de exemplo, pois ainda não há loader BigQuery → operacoes_comex.

---

## 3b. (removido – conteúdo já está na seção 3)

- Hoje o projeto usa **BigQuery** (Base dos Dados) para coisas como estabelecimentos → tabela `Empresa`; não há loader que grave dados do BigQuery direto em `operacoes_comex`.
- O **dashboard e os filtros por empresa** dependem do **PostgreSQL (ou SQLite)** com a tabela `operacoes_comex` e campos de empresa.
- **Opção “tudo no BigQuery”:** tecnicamente possível no longo prazo (ler dados do BigQuery no backend e até cache em memória/SQLite), mas exige refatoração maior. Não resolve o “banco fora do ar” de forma rápida.

Ou seja: a saída **rápida** é repor o PostgreSQL (Neon/Supabase free) e, se quiser, subir o backend para Basic-1gb. BigQuery continua como fonte complementar, sem precisar mudar tudo agora.

---

## 4. Passo a passo rápido (opção A + Basic-1gb, se quiser pagar o backend)

1. **Criar banco gratuito**
   - Acesse [Neon](https://neon.tech) ou [Supabase](https://supabase.com).
   - Crie um projeto e um banco PostgreSQL.
   - Copie a **connection string** (formato `postgresql://user:password@host/dbname?sslmode=require`).

2. **Configurar no Render**
   - No serviço do **backend** (comex-backend): **Environment** → adicione/edite `DATABASE_URL` com a URL copiada.
   - (Opcional) Se usar Neon/Supabase, não crie “PostgreSQL” no Render; use só o serviço web.

3. **Rodar migrações / recriar tabelas**
   - Na primeira vez com o novo banco, é preciso criar tabelas (Alembic ou script de criação). Se você já tiver migrations, rode no ambiente do Render ou local apontando para a nova `DATABASE_URL`.

4. **Reimportar dados (se necessário)**
   - Se o banco antigo foi perdido, reimporte o Excel ou os dados de exemplo conforme você já faz (ex.: upload do Excel ou script `popular_dados_exemplo.py`) para o novo banco.

5. **Escolher plano do backend (se o free acabou)**
   - Se o **serviço web** também parou por fim de free tier: no Render, no serviço do backend, altere o plano para **Basic-1gb ($19/mês)** se quiser estabilidade boa para o projeto.

---

## 5. Resumo final

- **Banco fora do ar:** use um **PostgreSQL gratuito** (Neon ou Supabase) e configure `DATABASE_URL` no Render. Não é obrigatório pagar pelo banco no Render.
- **Plano no Render (serviço web):** se for pagar, o mais indicado para o seu projeto é o **Basic-1gb ($19/mês)**. Basic-256mb ($6) só como opção mais barata e com menos margem.
- **BigQuery:** continua como fonte de dados (estabelecimentos etc.); não substitui, no curto prazo, o PostgreSQL para o dashboard e filtros por empresa.

Se quiser, no próximo passo podemos detalhar só a criação do banco no Neon (ou Supabase) e o formato exato da `DATABASE_URL` para colar no Render.
