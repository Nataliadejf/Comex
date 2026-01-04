# 🚀 PASSO A PASSO: Como Popular o Dashboard com Dados

## ⚡ Método Rápido (Recomendado)

### 📥 PASSO 1: Baixar Arquivos CSV

1. **Acesse o portal Comex Stat:**
   - URL: https://comexstat.mdic.gov.br/
   - Ou: https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/

2. **Baixe os arquivos CSV:**
   - **Exportação**: `EXP_2025.csv` (ou `EXP_YYYY.csv`)
   - **Importação**: `IMP_2025.csv` (ou `IMP_YYYY.csv`)
   
   💡 **Dica**: Baixe pelo menos os últimos 3 meses de dados

3. **Salve os arquivos em uma destas pastas:**
   ```
   D:\comex\2025\
   ```
   OU
   ```
   D:\NatFranca\raw\
   ```
   
   📁 **Estrutura esperada:**
   ```
   D:\comex\2025\
   ├── EXP_2025.csv
   ├── IMP_2025.csv
   └── ...
   ```

---

### 🔄 PASSO 2: Processar os Arquivos CSV

Abra o PowerShell e execute:

```powershell
# 1. Navegar para a pasta do backend
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend

# 2. Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# 3. Processar os arquivos CSV
python scripts/process_files.py
```

**O que acontece:**
- ✅ O script procura arquivos CSV nas pastas configuradas
- ✅ Identifica automaticamente se é Importação ou Exportação
- ✅ Extrai o mês de referência do nome do arquivo
- ✅ Processa e importa para o banco de dados SQLite
- ✅ Mostra progresso e estatísticas

**Exemplo de saída esperada:**
```
Processando arquivo: EXP_2025.csv
Tipo identificado: Exportação
Mês identificado: 2025-01
✅ 15.234 registros processados e salvos
```

---

### ✅ PASSO 3: Verificar se os Dados Foram Importados

Execute este comando para verificar:

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); count = db.query(func.count(OperacaoComex.id)).scalar(); print(f'✅ Total de registros no banco: {count:,}')"
```

**Se mostrar um número maior que 0, está funcionando!** ✅

Para ver mais detalhes:

```powershell
# Ver registros por tipo
python -c "from database import get_db, OperacaoComex, TipoOperacao; from sqlalchemy import func; db = next(get_db()); imp = db.query(func.count(OperacaoComex.id)).filter(OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO).scalar(); exp = db.query(func.count(OperacaoComex.id)).filter(OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO).scalar(); print(f'📊 Importações: {imp:,} | Exportações: {exp:,}')"
```

---

### 🌐 PASSO 4: Visualizar no Dashboard

1. **Inicie o Backend** (se não estiver rodando):

   ```powershell
   # Na pasta backend
   python run.py
   ```
   
   Você deve ver:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

2. **Inicie o Frontend** (em outro terminal):

   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\frontend
   npm start
   ```
   
   O navegador abrirá automaticamente em: **http://localhost:3000**

3. **Use o Dashboard:**
   - Os dados devem aparecer automaticamente
   - Use os filtros (Período, NCM, Tipo, Empresa)
   - Clique em "Buscar Dados" para aplicar filtros
   - Clique em "Exportar Relatório" para baixar Excel

---

## 🎯 Resumo Visual

```
┌─────────────────────────────────────────┐
│  1. BAIXAR CSV                          │
│     Portal Comex Stat                   │
│     → Salvar em D:\comex\2025\         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. PROCESSAR                           │
│     python scripts/process_files.py     │
│     → Importa para banco SQLite        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. VERIFICAR                           │
│     python -c "..."                     │
│     → Confirma registros importados    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  4. VISUALIZAR                          │
│     Backend: python run.py              │
│     Frontend: npm start                 │
│     → http://localhost:3000            │
└─────────────────────────────────────────┘
```

---

## 🔧 Comandos Úteis

### Verificar Status do Banco:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); count = db.query(func.count(OperacaoComex.id)).scalar(); print(f'📊 Total: {count:,} registros')"
```

### Recriar Banco (se corrompido):

```powershell
python scripts/recriar_banco.py
python scripts/process_files.py
```

### Processar Arquivo Específico:

```powershell
python scripts/process_single_file.py "D:\comex\2025\EXP_2025.csv"
```

---

## ⚠️ Problemas Comuns

### ❌ "Nenhum arquivo encontrado"

**Solução:**
- Verifique se os arquivos estão em `D:\comex\2025\` ou `D:\NatFranca\raw\`
- Verifique se os nomes estão corretos: `EXP_2025.csv` ou `IMP_2025.csv`

### ❌ "Erro ao processar arquivo"

**Solução:**
- Verifique se o arquivo CSV não está corrompido
- Tente baixar novamente do portal
- Verifique se o arquivo tem o formato correto (separador `;`)

### ❌ "Banco de dados corrompido"

**Solução:**
```powershell
python scripts/recriar_banco.py
python scripts/process_files.py
```

### ❌ "Dashboard mostra zero"

**Solução:**
1. Verifique se há dados no banco (comando acima)
2. Se houver dados, reinicie o backend
3. Limpe o cache do navegador (Ctrl+F5)

---

## 📝 Checklist Rápido

- [ ] Arquivos CSV baixados do portal
- [ ] Arquivos salvos em `D:\comex\2025\` ou `D:\NatFranca\raw\`
- [ ] Script `process_files.py` executado com sucesso
- [ ] Verificação mostra registros > 0
- [ ] Backend rodando (`python run.py`)
- [ ] Frontend rodando (`npm start`)
- [ ] Dashboard acessível em http://localhost:3000
- [ ] Dados aparecendo no dashboard

---

## 🎉 Pronto!

Após seguir estes passos, seu dashboard estará populado com dados e pronto para uso!

**Próximos passos:**
- ✅ Use os filtros para análises específicas
- ✅ Exporte relatórios em Excel
- ✅ Analise gráficos e estatísticas
- ✅ Compare períodos diferentes

---

## 📞 Precisa de Ajuda?

Consulte também:
- `COMO_POPULAR_DASHBOARD.md` - Guia completo e detalhado
- `README.md` - Documentação geral do projeto



