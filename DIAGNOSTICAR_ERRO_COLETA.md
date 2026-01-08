# 🔍 Diagnosticar Erro na Coleta Enriquecida

## 📋 Passo 1: Executar Teste Diagnóstico

Execute o script de teste que vai verificar cada etapa:

```bash
TESTAR_COLETA.bat
```

Este script vai:
1. ✅ Testar criação do coletor
2. ✅ Testar download de tabelas
3. ✅ Testar download de dados mensais
4. ✅ Testar processamento de CSV
5. ✅ Testar coleta completa (1 mês apenas)

## 🔧 Erros Comuns e Soluções

### Erro: "pandas não disponível"

**Solução**:
```bash
pip install pandas openpyxl
```

### Erro: "ModuleNotFoundError: No module named 'data_collector'"

**Solução**:
- Certifique-se de estar no diretório correto
- Execute do diretório `backend/`:
```bash
cd backend
python -m data_collector.enriched_collector
```

### Erro: "Connection timeout" ou "Failed to download"

**Solução**:
- Verifique sua conexão com internet
- Tente novamente (pode ser temporário)
- Verifique se o portal MDIC está acessível:
  - https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/

### Erro: "PermissionError" ou "Access denied"

**Solução**:
- Verifique permissões de escrita na pasta `data/`
- Execute como administrador se necessário

### Erro: "Database locked" ou "OperationalError"

**Solução**:
- Feche outras conexões com o banco
- Reinicie o backend
- Verifique se não há outro processo usando o banco

### Erro: "KeyError" ou "AttributeError"

**Solução**:
- O formato do CSV pode ter mudado
- Verifique os logs para ver qual campo está faltando
- Pode precisar atualizar o transformer

## 📊 Verificar Logs Detalhados

Execute com logs detalhados:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from backend.data_collector.enriched_collector import EnrichedDataCollector
from backend.database import get_db
import asyncio

async def coletar():
    db = next(get_db())
    collector = EnrichedDataCollector()
    stats = await collector.collect_and_enrich(db, meses=1)
    print(stats)

asyncio.run(coletar())
```

## 🐛 Enviar Informações do Erro

Para ajudar a diagnosticar, envie:

1. **Mensagem de erro completa** (copy/paste)
2. **Stack trace** (se houver)
3. **Logs do backend** (últimas 50 linhas)
4. **Versão do Python**: `python --version`
5. **Pacotes instalados**: `pip list | findstr pandas`

## ✅ Teste Rápido

Teste apenas o download de um arquivo:

```python
import asyncio
from backend.data_collector.mdic_csv_collector import MDICCSVCollector

async def testar():
    collector = MDICCSVCollector()
    from datetime import datetime
    hoje = datetime.now()
    arquivos = await collector.download_monthly_data(hoje.year, hoje.month, "importacao")
    print(f"Arquivos baixados: {arquivos}")

asyncio.run(testar())
```

---

**Execute `TESTAR_COLETA.bat` e envie o resultado completo do erro!**



