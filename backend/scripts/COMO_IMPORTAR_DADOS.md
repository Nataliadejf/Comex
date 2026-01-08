# 📥 Como Importar Dados Excel para PostgreSQL

Este guia explica como importar os arquivos Excel para o PostgreSQL no Render.

## 📋 Pré-requisitos

1. ✅ PostgreSQL criado no Render
2. ✅ `DATABASE_URL` configurada no backend
3. ✅ Arquivos Excel disponíveis

## 📁 Localização dos Arquivos

Os arquivos devem estar em um dos seguintes locais:

### Opção 1: No projeto local (recomendado para desenvolvimento)
```
projeto_comex/
├── comex_data/
│   └── comexstat_csv/
│       ├── H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx
│       └── Empresas Importadoras e Exportadoras.xlsx
```

### Opção 2: Na pasta backend/data (para deploy)
```
projeto_comex/
└── backend/
    └── data/
        ├── H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx
        └── Empresas Importadoras e Exportadoras.xlsx
```

## 🚀 Método 1: Importação Local (Desenvolvimento)

### Passo 1: Preparar ambiente local

```bash
# No diretório do projeto
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex

# Instalar dependências (se ainda não instalou)
pip install -r backend/requirements-render-ultra-minimal.txt
```

### Passo 2: Configurar DATABASE_URL localmente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
```

Ou configure diretamente no código temporariamente para teste.

### Passo 3: Executar importação

```bash
cd backend
python scripts/import_data.py
```

## 🚀 Método 2: Importação no Render (Produção)

### Passo 1: Fazer upload dos arquivos Excel

**Opção A: Via Git (Recomendado)**

1. Copie os arquivos Excel para `backend/data/`:
   ```bash
   mkdir -p backend/data
   cp "comex_data/comexstat_csv/H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" backend/data/
   cp "comex_data/comexstat_csv/Empresas Importadoras e Exportadoras.xlsx" backend/data/
   ```

2. Commit e push:
   ```bash
   git add backend/data/*.xlsx
   git commit -m "feat: Adicionar arquivos Excel para importação"
   git push origin main
   ```

**Opção B: Via Shell do Render**

1. No Render Dashboard → `comex-backend` → **Shell**
2. Execute:
   ```bash
   mkdir -p /opt/render/project/src/backend/data
   ```
3. Faça upload dos arquivos via SFTP/SCP ou outro método

### Passo 2: Executar importação no Render

1. No Render Dashboard → `comex-backend` → **Shell**
2. Execute:
   ```bash
   cd /opt/render/project/src/backend
   python scripts/import_data.py
   ```

## 🔍 Verificar Importação

Após a importação, verifique os dados:

```bash
# No Shell do Render ou localmente
python -c "
from database.database import SessionLocal
from database.models import ComercioExterior, Empresa
db = SessionLocal()
print(f'✅ Registros ComercioExterior: {db.query(ComercioExterior).count()}')
print(f'✅ Empresas: {db.query(Empresa).count()}')
db.close()
"
```

Ou teste o endpoint:

```bash
curl https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24
```

## ⚠️ Troubleshooting

### Erro: "Arquivo não encontrado"

**Solução:**
- Verifique se os arquivos estão nos caminhos corretos
- O script tenta múltiplos caminhos automaticamente
- Verifique os logs para ver quais caminhos foram tentados

### Erro: "Connection refused" ou "could not connect"

**Solução:**
- Verifique se `DATABASE_URL` está configurada corretamente
- Certifique-se de que o PostgreSQL está rodando
- Use "Internal Database URL" (não External) no Render

### Erro: "Table does not exist"

**Solução:**
- Execute o schema SQL manualmente:
  ```bash
  psql $DATABASE_URL -f backend/database/schema.sql
  ```
- Ou o script cria automaticamente via SQLAlchemy

### Importação muito lenta

**Solução:**
- O script já faz commit a cada 1000 registros
- Para arquivos muito grandes, considere dividir em lotes menores
- Use transações maiores se necessário (modificar o script)

## 📊 Estrutura Esperada dos Arquivos Excel

### Arquivo: H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx

**Colunas esperadas:**
- `Mês` - String (ex: "12. Dezembro")
- `Código NCM` - String (8 dígitos)
- `Descrição NCM` - String
- `UF do Produto` - String (2 caracteres)
- `Países` - String
- `Exportação - 2025 - Valor US$ FOB` - Number
- `Exportação - 2025 - Quilograma Líquido` - Number
- `Importação - 2025 - Valor US$ FOB` - Number
- `Importação - 2025 - Quilograma Líquido` - Number

### Arquivo: Empresas Importadoras e Exportadoras.xlsx

**Colunas esperadas (flexível):**
- `CNPJ` ou `cnpj` - String
- `Razão Social` ou `Nome` ou `Empresa` - String
- `CNAE` ou `cnae` - String
- `Estado` ou `UF` - String (2 caracteres)
- `Valor Importação` ou `Importado (R$)` - Number (opcional)
- `Valor Exportação` ou `Exportado (R$)` - Number (opcional)

## ✅ Checklist Final

- [ ] PostgreSQL criado no Render
- [ ] `DATABASE_URL` configurada no backend
- [ ] Arquivos Excel copiados para `backend/data/` ou `comex_data/comexstat_csv/`
- [ ] Schema SQL executado (ou tabelas criadas via SQLAlchemy)
- [ ] Script de importação executado
- [ ] Dados verificados no banco
- [ ] Endpoint `/dashboard/stats` retornando dados

## 🎯 Resultado Esperado

Após a importação bem-sucedida:

- ✅ Tabela `comex_registros` com milhares de registros
- ✅ Tabela `empresas` com empresas importadoras/exportadoras
- ✅ Endpoint `/dashboard/stats` retornando dados reais
- ✅ Dashboard populado com informações
