# 📊 Como Popular o Dashboard com Dados - Guia Completo

## 🎯 Visão Geral

Existem **3 formas** de popular o dashboard com dados do Comex Stat:

1. **Via API do Comex Stat** (automático - se API estiver disponível)
2. **Via Download Manual de CSV** (recomendado - mais confiável)
3. **Via Scripts Automáticos** (fallback)

---

## 📋 MÉTODO 1: Via API do Comex Stat (Automático)

### Pré-requisitos:
- API do Comex Stat configurada e disponível
- Credenciais de acesso (se necessário)

### Passo a Passo:

#### 1. Configurar a API (se necessário)

Crie/edite o arquivo `.env` na pasta `backend`:

```env
COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
COMEX_STAT_API_KEY=sua_chave_aqui
```

#### 2. Iniciar o Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python run.py
```

#### 3. Usar o Dashboard

- O sistema tentará coletar dados automaticamente quando você:
  - Abrir o dashboard pela primeira vez
  - Clicar em "Buscar Dados" sem filtros
  - Clicar em "Atualizar Dashboard"

**Vantagens:**
- ✅ Automático
- ✅ Sem necessidade de download manual
- ✅ Dados sempre atualizados

**Desvantagens:**
- ⚠️ Requer API configurada e disponível
- ⚠️ Pode ter limitações de rate limit

---

## 📋 MÉTODO 2: Via Download Manual de CSV (RECOMENDADO)

Este é o método mais confiável e funciona sempre!

### Passo a Passo Completo:

#### **PASSO 1: Baixar Arquivos CSV do Portal Comex Stat**

1. Acesse o portal: **https://comexstat.mdic.gov.br/**

2. Navegue até a seção de **"Dados"** ou **"Download"**

3. Baixe os arquivos CSV dos últimos 3 meses:
   - **Exportação**: `EXP_YYYY.csv` (ex: `EXP_2025.csv`)
   - **Importação**: `IMP_YYYY.csv` (ex: `IMP_2025.csv`)

   Ou baixe por mês:
   - `EXP_2025_01.csv` (Exportação de Janeiro/2025)
   - `IMP_2025_01.csv` (Importação de Janeiro/2025)

4. **Salve os arquivos** na pasta:
   ```
   D:\comex\2025\
   ```
   
   Ou se preferir usar a pasta configurada:
   ```
   D:\NatFranca\raw\
   ```

#### **PASSO 2: Processar os Arquivos CSV**

Você tem **2 opções**:

##### **Opção A: Processar Todos os Arquivos de Uma Vez**

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/process_files.py
```

Este script vai:
- ✅ Procurar todos os arquivos CSV em `D:\comex\` ou `D:\NatFranca\raw\`
- ✅ Identificar automaticamente o tipo (Importação/Exportação)
- ✅ Extrair o mês de referência
- ✅ Processar e importar para o banco de dados

##### **Opção B: Processar Um Arquivo Específico**

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/process_single_file.py "D:\comex\2025\EXP_2025.csv"
```

#### **PASSO 3: Verificar se os Dados Foram Importados**

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); count = db.query(func.count(OperacaoComex.id)).scalar(); print(f'Total de registros: {count}')"
```

Se mostrar um número maior que 0, os dados foram importados! ✅

#### **PASSO 4: Visualizar no Dashboard**

1. Inicie o backend (se não estiver rodando):
   ```powershell
   python run.py
   ```

2. Inicie o frontend:
   ```powershell
   cd ..\frontend
   npm start
   ```

3. Acesse: **http://localhost:3000**

4. O dashboard deve mostrar os dados importados! 🎉

---

## 📋 MÉTODO 3: Via Scripts Automáticos (Fallback)

### Script Completo (Tenta API → Download → Processar CSV)

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/sistema_completo.py
```

Este script:
1. Recria o banco de dados (faz backup do antigo)
2. Tenta coletar via API
3. Tenta download automático
4. Processa arquivos CSV manuais

---

## 🔍 Verificando se os Dados Estão no Banco

### Verificar Total de Registros:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); count = db.query(func.count(OperacaoComex.id)).scalar(); print(f'✅ Total de registros: {count:,}')"
```

### Verificar Registros por Tipo:

```powershell
python -c "from database import get_db, OperacaoComex, TipoOperacao; from sqlalchemy import func; db = next(get_db()); imp = db.query(func.count(OperacaoComex.id)).filter(OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO).scalar(); exp = db.query(func.count(OperacaoComex.id)).filter(OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO).scalar(); print(f'Importações: {imp:,} | Exportações: {exp:,}')"
```

### Verificar Registros por Mês:

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); meses = db.query(OperacaoComex.mes_referencia, func.count(OperacaoComex.id)).group_by(OperacaoComex.mes_referencia).all(); print('Registros por mês:'); [print(f'  {mes}: {count:,}') for mes, count in meses]"
```

---

## 🎯 Fluxo Recomendado (Passo a Passo Simplificado)

### Para Começar Agora:

1. **Baixe os arquivos CSV** do portal Comex Stat
   - Salve em: `D:\comex\2025\` ou `D:\NatFranca\raw\`

2. **Processe os arquivos**:
   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
   .\venv\Scripts\Activate.ps1
   python scripts/process_files.py
   ```

3. **Verifique os dados**:
   ```powershell
   python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); print(f'Registros: {db.query(func.count(OperacaoComex.id)).scalar():,}')"
   ```

4. **Inicie o backend** (se não estiver rodando):
   ```powershell
   python run.py
   ```

5. **Inicie o frontend**:
   ```powershell
   cd ..\frontend
   npm start
   ```

6. **Acesse o dashboard**: http://localhost:3000

7. **Use os filtros**:
   - Período
   - NCM (ex: 84295200)
   - Tipo de Operação
   - Nome da Empresa
   - Clique em "Buscar Dados"

8. **Exporte relatórios**:
   - Clique em "Exportar Relatório" no header

---

## 📁 Estrutura de Pastas Esperada

```
D:\comex\
└── 2025\
    ├── EXP_2025.csv          (Exportações de 2025)
    ├── IMP_2025.csv          (Importações de 2025)
    └── ...

OU

D:\NatFranca\
└── raw\
    ├── 2025-01\
    │   ├── EXP_2025.csv
    │   └── IMP_2025.csv
    └── ...
```

---

## ⚠️ Problemas Comuns e Soluções

### Problema: "Nenhum dado disponível"

**Solução:**
1. Verifique se há arquivos CSV na pasta configurada
2. Execute o script de processamento
3. Verifique se os dados foram importados (comando acima)

### Problema: "Erro ao processar arquivo"

**Solução:**
1. Verifique se o arquivo CSV está no formato correto
2. Verifique se o arquivo não está corrompido
3. Tente processar um arquivo por vez

### Problema: "Banco de dados corrompido"

**Solução:**
```powershell
python scripts/recriar_banco.py
python scripts/process_files.py
```

---

## 📞 Próximos Passos

Após popular o dashboard:

1. ✅ Use os filtros para buscar dados específicos
2. ✅ Exporte relatórios em Excel
3. ✅ Analise gráficos e estatísticas
4. ✅ Faça comparações período a período

---

## 🎉 Resumo Rápido

**Para popular AGORA:**

1. Baixe CSV do portal → Salve em `D:\comex\2025\`
2. Execute: `python scripts/process_files.py`
3. Verifique: `python -c "..."` (comando acima)
4. Acesse: http://localhost:3000

**Pronto!** 🚀



