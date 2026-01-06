# 🚀 Próximos Passos - Coleta de Dados Enriquecidos

## ✅ O que já está pronto

1. ✅ Sistema de coleta CSV do MDIC implementado
2. ✅ Integração com empresas do MDIC
3. ✅ Integração com CNAE para sugestões
4. ✅ Autocomplete atualizado
5. ✅ Scheduler configurado
6. ✅ Endpoints da API criados

## 📋 Passo 1: Executar Coleta Inicial

### Opção A: Via Script Batch (Mais Fácil)

1. **Execute o arquivo**:
   ```
   EXECUTAR_COLETA_ENRIQUECIDA.bat
   ```

2. **Aguarde a conclusão**:
   - Pode levar de 1 a 4 horas na primeira execução
   - Depende da velocidade da internet
   - Você verá o progresso no console

### Opção B: Via API (Recomendado para produção)

1. **Certifique-se que o backend está rodando**:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Execute a coleta via API**:
   ```bash
   curl -X POST "http://localhost:8000/coletar-dados-enriquecidos?meses=24"
   ```

   Ou use o Postman/Insomnia:
   - **Método**: POST
   - **URL**: `http://localhost:8000/coletar-dados-enriquecidos?meses=24`
   - **Headers**: `Content-Type: application/json`

### Opção C: Via Python Direto

```python
import asyncio
from backend.data_collector.enriched_collector import EnrichedDataCollector
from backend.database import get_db

async def coletar():
    db = next(get_db())
    collector = EnrichedDataCollector()
    
    print("Iniciando coleta enriquecida...")
    stats = await collector.collect_and_enrich(db, meses=24)
    
    print("\n" + "="*60)
    print("COLETA CONCLUÍDA!")
    print("="*60)
    print(f"Total de registros: {stats['total_registros']:,}")
    print(f"Registros novos: {stats['registros_novos']:,}")
    print(f"Registros atualizados: {stats['registros_atualizados']:,}")
    print(f"Empresas enriquecidas: {stats['empresas_enriquecidas']:,}")
    print(f"Meses processados: {len(stats['meses_processados'])}")
    print("="*60)

asyncio.run(coletar())
```

## 📊 Passo 2: Verificar Resultados

### Verificar no Banco de Dados

```python
from backend.database import get_db, OperacaoComex
from sqlalchemy import func

db = next(get_db())

# Total de registros
total = db.query(func.count(OperacaoComex.id)).scalar()
print(f"Total de operações: {total:,}")

# Empresas únicas
importadoras = db.query(func.count(func.distinct(OperacaoComex.razao_social_importador))).filter(
    OperacaoComex.razao_social_importador.isnot(None)
).scalar()
print(f"Empresas importadoras únicas: {importadoras:,}")

exportadoras = db.query(func.count(func.distinct(OperacaoComex.razao_social_exportador))).filter(
    OperacaoComex.razao_social_exportador.isnot(None)
).scalar()
print(f"Empresas exportadoras únicas: {exportadoras:,}")
```

### Verificar via API

```bash
# Verificar estatísticas do dashboard
GET http://localhost:8000/dashboard/stats

# Testar autocomplete
GET http://localhost:8000/empresas/autocomplete/importadoras?q=
GET http://localhost:8000/empresas/autocomplete/exportadoras?q=
```

## 🎯 Passo 3: Testar no Dashboard

1. **Acesse o dashboard**:
   - Frontend: `http://localhost:3000` (ou URL do Render)
   - Faça login

2. **Teste os campos de autocomplete**:
   - Clique em "Provável Importador"
   - Deve aparecer lista de empresas sugeridas
   - Digite para filtrar
   - Repita para "Provável Exportador"

3. **Teste a busca**:
   - Selecione um período (ex: últimos 2 anos)
   - Clique em "Buscar"
   - Verifique se os gráficos mostram dados
   - Verifique se a tabela tem registros

## 🔄 Passo 4: Configurar Atualizações Automáticas

O scheduler já está configurado para:
- **Coleta diária**: 02:00 (último mês)
- **Empresas MDIC**: Domingo 03:00 (semanal)
- **Relacionamentos**: 03:30 (diário)
- **Sinergias**: 04:00 (diário)

**Não precisa fazer nada** - funciona automaticamente quando o backend está rodando.

## ⚠️ Troubleshooting

### Problema: Coleta muito lenta
**Solução**: 
- Reduza o número de meses: `meses=12` ao invés de `24`
- Execute em horários de menor tráfego
- Verifique sua conexão com internet

### Problema: Erro ao baixar arquivos
**Solução**:
- Verifique conexão com internet
- Tente novamente (pode ser temporário)
- Verifique se o portal MDIC está acessível

### Problema: Autocomplete vazio
**Solução**:
- Execute a coleta primeiro
- Verifique se há dados no banco
- Tente sem filtros primeiro (`q=`)

### Problema: Dashboard sem dados
**Solução**:
- Verifique se a coleta foi concluída
- Verifique os logs do backend
- Tente buscar sem filtros de NCM

## 📈 Monitoramento

### Acompanhar Progresso

Os logs do backend mostram:
```
✅ Baixado: IMP_2024_01.csv (2.5 MB)
✅ Processados 15.234 registros de IMP_2024_01.csv
✅ Empresas MDIC atualizadas: 5.000 empresas
✅ Coleta enriquecida concluída: 150.000 registros
```

### Verificar Status

```bash
# Health check
GET http://localhost:8000/health

# Estatísticas de coleta
GET http://localhost:8000/estatisticas-cruzamento
```

## 🎉 Próximos Passos Após Coleta

1. ✅ **Testar autocomplete** - Verificar se empresas aparecem
2. ✅ **Testar dashboard** - Verificar se gráficos mostram dados
3. ✅ **Testar busca** - Verificar se filtros funcionam
4. ✅ **Verificar sinergias** - Ver se sugestões aparecem
5. ✅ **Deploy no Render** - Após testar localmente

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do backend
2. Verifique se o banco tem dados
3. Tente executar a coleta novamente
4. Verifique a documentação em `COLETAR_DADOS_MDIC_ENRIQUECIDOS.md`

---

**Recomendação**: Comece executando `EXECUTAR_COLETA_ENRIQUECIDA.bat` e aguarde a conclusão antes de testar o dashboard.

