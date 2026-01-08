# 📥 Como Importar Dados Excel para SQLite Local e depois PostgreSQL

Este guia explica como importar os arquivos Excel da sua máquina para o banco de dados local (SQLite) e depois migrar para PostgreSQL no Render.

## 📋 Pré-requisitos

1. ✅ Arquivos Excel na pasta `backend/data/`:
   - `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
   - `Empresas Importadoras e Exportadoras.xlsx`

2. ✅ Python instalado com pandas e openpyxl

## 🚀 Passo 1: Importar para SQLite Local

Execute o script de importação local:

```bash
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
python backend/scripts/importar_excel_local.py
```

### O que este script faz:

1. ✅ Cria banco SQLite em `comex_data/database/comex.db`
2. ✅ Cria todas as tabelas necessárias
3. ✅ Importa dados do arquivo de Comércio Exterior
4. ✅ Importa dados do arquivo de Empresas
5. ✅ Mostra totais de importação e exportação

### Exemplo de saída:

```
════════════════════════════════════════════════════════════════════════════════
IMPORTAÇÃO PARA SQLITE LOCAL
Banco de dados: C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\database\comex.db
════════════════════════════════════════════════════════════════════════════════

📄 Lendo arquivo Excel: H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx
✅ Arquivo lido: 50000 linhas, 10 colunas

════════════════════════════════════════════════════════════════════════════════
✅ IMPORTAÇÃO DE COMÉRCIO EXTERIOR CONCLUÍDA
════════════════════════════════════════════════════════════════════════════════
📊 Total de registros inseridos: 100,000
💰 Total Importação (USD): $50,000,000.00
💰 Total Exportação (USD): $30,000,000.00
📦 Total Peso Importação (kg): 1,000,000.00
📦 Total Peso Exportação (kg): 500,000.00
════════════════════════════════════════════════════════════════════════════════
```

## 🚀 Passo 2: Migrar para PostgreSQL no Render

Após importar para SQLite local, configure a `DATABASE_URL` do PostgreSQL e execute a migração:

### 2.1. Obter URL do PostgreSQL no Render

1. Acesse o Render Dashboard
2. Vá em **PostgreSQL** → Seu banco → **Connections**
3. Copie a **Internal Database URL**

### 2.2. Configurar DATABASE_URL

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://user:password@host:port/dbname"
```

**Windows CMD:**
```cmd
set DATABASE_URL=postgresql://user:password@host:port/dbname
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://user:password@host:port/dbname"
```

### 2.3. Executar Migração

```bash
python backend/scripts/migrar_para_postgresql.py
```

### Exemplo de saída:

```
════════════════════════════════════════════════════════════════════════════════
MIGRAÇÃO SQLITE → POSTGRESQL
════════════════════════════════════════════════════════════════════════════════
📁 SQLite local: C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\database\comex.db
📁 PostgreSQL: postgresql://user:pass@host:port/db...

🔨 Criando tabelas no PostgreSQL...
✅ Tabelas criadas

📊 Migrando dados de Comércio Exterior...
  📋 Encontrados 100,000 registros no SQLite
  ⏳ Migrados 1,000 registros...
  ⏳ Migrados 2,000 registros...
  ...
✅ 100,000 registros de Comércio Exterior migrados

🏢 Migrando dados de Empresas...
  📋 Encontradas 500 empresas no SQLite
✅ 500 empresas migradas

════════════════════════════════════════════════════════════════════════════════
📊 RESUMO DA MIGRAÇÃO
════════════════════════════════════════════════════════════════════════════════
📊 Registros de Comércio Exterior: 100,000
🏢 Empresas: 500
💰 Total Importação (USD): $50,000,000.00
💰 Total Exportação (USD): $30,000,000.00
💰 Valor Total (USD): $80,000,000.00
════════════════════════════════════════════════════════════════════════════════
✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!

💡 Agora o dashboard deve mostrar os dados!
════════════════════════════════════════════════════════════════════════════════
```

## ✅ Verificar Dados no Dashboard

Após a migração, acesse o dashboard:

```
https://comex-backend-wjco.onrender.com/dashboard/stats
```

O endpoint deve retornar os dados com os totais de importação e exportação.

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"

**Solução:**
- Verifique se os arquivos Excel estão em `backend/data/`
- Verifique os nomes dos arquivos (devem ser exatamente como especificado)

### Erro: "DATABASE_URL não configurada"

**Solução:**
- Configure a variável `DATABASE_URL` antes de executar a migração
- Verifique se a URL está correta (deve começar com `postgresql://`)

### Erro: "could not translate host name"

**Solução:**
- Use a **Internal Database URL** (não External)
- Certifique-se de que o PostgreSQL está na mesma região do backend

### Dashboard ainda vazio após migração

**Solução:**
1. Verifique os logs do backend no Render
2. Execute: `GET /api/analise/verificar-dados` para verificar se há dados
3. Verifique se o endpoint `/dashboard/stats` está buscando das tabelas corretas

## 📊 Scripts Disponíveis

1. **`importar_excel_local.py`** - Importa Excel → SQLite local
2. **`migrar_para_postgresql.py`** - Migra SQLite → PostgreSQL
3. **`verificar_dados.py`** - Verifica dados em todas as tabelas

## 💡 Dicas

- ✅ Sempre execute primeiro `importar_excel_local.py` para testar localmente
- ✅ Verifique os totais no SQLite antes de migrar
- ✅ O script de migração mostra os totais durante o processo
- ✅ Os logs do dashboard mostram os totais quando acessado
