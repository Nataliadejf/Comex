# 🔧 Configurar Dados Reais - Comex Stat

Este guia explica como configurar a integração com dados **REAIS** do portal Comex Stat.

## 📋 Opções Disponíveis

### Opção 1: Download Manual + Processamento (Recomendado)

#### Passo 1: Baixar Arquivos CSV

1. Acesse: **https://comexstat.mdic.gov.br**
2. Navegue até: **Dados Abertos > Download**
3. Baixe os arquivos CSV:
   - **Exportação** (últimos 3 meses)
   - **Importação** (últimos 3 meses)
4. Salve os arquivos em:
   ```
   C:\Users\User\Desktop\Cursor\Projetos\data\raw\
   ```
   Ou:
   ```
   D:\NatFranca\raw\
   ```

**Formato esperado:**
- `EXP_2025_01.csv` (Exportação de Janeiro 2025)
- `IMP_2025_01.csv` (Importação de Janeiro 2025)

#### Passo 2: Processar Arquivos

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/process_files.py
```

### Opção 2: Download Automático

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/integrar_api_real.py
```

Este script:
- ✅ Remove dados de exemplo
- ✅ Tenta baixar dados reais do portal
- ✅ Salva arquivos CSV para processamento

### Opção 3: Configurar API (Se Disponível)

Se você tiver credenciais da API oficial:

1. Edite `backend/.env`:
```env
COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
COMEX_STAT_API_KEY=sua_chave_aqui
```

2. Execute:
```powershell
python scripts/integrar_api_real.py
```

## 🗄️ Configurar MySQL/PostgreSQL (Opcional)

### MySQL Workbench

1. **Gerar Script SQL:**
```powershell
python scripts/configurar_banco_mysql.py
```

2. **No MySQL Workbench:**
   - Abra o arquivo: `scripts/sql/create_tables_mysql.sql`
   - Execute o script (Ctrl+Shift+Enter)

3. **Configurar Conexão:**
   - Edite `backend/.env`:
   ```env
   DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/comex_analyzer
   ```

### PostgreSQL

1. **Gerar Script SQL:**
```powershell
python scripts/configurar_banco_mysql.py
```

2. **Executar Script:**
```bash
psql -U postgres -f scripts/sql/create_tables_postgresql.sql
```

3. **Configurar Conexão:**
   - Edite `backend/.env`:
   ```env
   DATABASE_URL=postgresql://usuario:senha@localhost:5432/comex_analyzer
   ```

## 🔄 Processo Completo

### 1. Remover Dados de Exemplo

```powershell
python scripts/integrar_api_real.py
```

### 2. Baixar Dados Reais

**Manual:**
- Baixe CSV do portal
- Salve em `data/raw/`

**Automático:**
- Execute `integrar_api_real.py`

### 3. Processar Arquivos

```powershell
python scripts/process_files.py
```

### 4. Verificar Dados

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); print(f'Total: {db.query(func.count(OperacaoComex.id)).scalar():,}')"
```

## 📊 Estrutura de Dados

Os dados reais do Comex Stat contêm:

- **NCM** (8 dígitos)
- **Descrição do Produto**
- **Tipo de Operação** (Importação/Exportação)
- **País de Origem/Destino**
- **UF** (Unidade Federativa)
- **Via de Transporte**
- **Valor FOB** (USD)
- **Peso Líquido/Bruto** (kg)
- **Data da Operação**
- **Mês de Referência**

## ⚠️ Importante

- ✅ Use sempre dados oficiais do portal Comex Stat
- ✅ Verifique a estrutura dos arquivos CSV antes de processar
- ✅ Mantenha backups do banco de dados
- ✅ Processe arquivos em ordem cronológica

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
**Solução:** Verifique se os arquivos estão na pasta correta

### Erro: "Formato inválido"
**Solução:** Verifique se o arquivo é CSV válido do Comex Stat

### Erro: "Banco de dados não conecta"
**Solução:** Verifique a URL de conexão no `.env`

---

**Última atualização**: Janeiro 2025



