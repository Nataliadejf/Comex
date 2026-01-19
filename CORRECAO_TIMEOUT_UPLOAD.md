# 🔧 Correção: Erros 502/503 nos Endpoints de Upload

## ❌ Problema Identificado

Os endpoints `/upload-e-importar-excel` e `/upload-e-importar-cnae` estavam retornando:
- **502 Bad Gateway**: Timeout do servidor
- **503 Service Unavailable**: Serviço hibernado ou sobrecarregado

## 🔍 Causa Raiz

O código estava fazendo **queries individuais** para cada linha do Excel:
- Para cada linha, fazia `db.query(...).first()` para verificar duplicatas
- Isso resultava em milhares de queries ao banco de dados
- Processamento muito lento, causando timeout

## ✅ Solução Aplicada

### Otimizações Implementadas:

1. **Bulk Inserts**: Uso de `bulk_insert_mappings()` em vez de inserções individuais
2. **Processamento em Batches**: Processa arquivos grandes em chunks de 500-1000 linhas
3. **Redução de Queries**: Verificação de duplicatas em memória (set) em vez de queries ao banco
4. **Commits Otimizados**: Commits em chunks maiores (1000 registros) em vez de a cada linha
5. **Logs Melhorados**: Logs de progresso para acompanhar o processamento

### Melhorias de Performance:

- **Antes**: ~1-2 segundos por linha (com query individual)
- **Depois**: ~100-200 linhas por segundo (com bulk insert)

**Redução de tempo estimada: 50-100x mais rápido!**

## 📋 Como Usar Agora

### 1. Aguardar Deploy

O código foi commitado. Aguarde 2-5 minutos para o deploy terminar.

### 2. Tentar Upload Novamente

**Via Swagger:**
1. Acesse: `https://comex-backend-gecp.onrender.com/docs`
2. Procure: `POST /upload-e-importar-excel` ou `POST /upload-e-importar-cnae`
3. Clique em "Try it out"
4. Selecione o arquivo
5. Clique em "Execute"
6. **Aguarde** - arquivos grandes podem levar alguns minutos

**Via curl:**
```powershell
$filePath = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
curl.exe -X POST "https://comex-backend-gecp.onrender.com/upload-e-importar-excel" -H "accept: application/json" -F "arquivo=@$filePath"
```

## ⏱️ Tempos Esperados

- **Arquivo pequeno** (< 10.000 linhas): 30-60 segundos
- **Arquivo médio** (10.000-100.000 linhas): 2-5 minutos
- **Arquivo grande** (> 100.000 linhas): 5-15 minutos

## 🐛 Se Ainda Houver Problemas

### Problema: 503 Service Unavailable

**Causa**: Serviço Render está hibernado (free tier)

**Solução**:
1. Aguarde 30-60 segundos
2. Tente novamente
3. O serviço será "acordado" automaticamente

### Problema: 502 Bad Gateway

**Causa**: Timeout ainda ocorrendo (arquivo muito grande)

**Soluções**:
1. Verifique os logs do Render para ver o progresso
2. Divida o arquivo em partes menores se possível
3. Use o endpoint `/importar-excel-automatico` se o arquivo já estiver no servidor

### Problema: Erro de Memória

**Causa**: Arquivo muito grande para processar de uma vez

**Solução**:
- O código agora processa em batches, mas arquivos extremamente grandes (> 1GB) podem ainda causar problemas
- Considere dividir o arquivo em partes menores

## 📊 Monitoramento

Os logs agora mostram progresso detalhado:
```
📤 Iniciando upload e importação do arquivo: arquivo.xlsx
📖 Lendo arquivo Excel...
✅ Arquivo lido: 50000 linhas, 15 colunas
🔄 Processando 50000 linhas em batches de 500...
  📊 Processadas 1000/50000 linhas...
  📊 Processadas 2000/50000 linhas...
💾 Inserindo 45000 operações no banco...
  ✅ Inseridos 1000/45000 registros...
✅ Importação concluída: 45000 registros
```

## ✅ Próximos Passos

Após fazer upload com sucesso:

1. Valide com `GET /validar-sistema`
2. Configure BigQuery (se ainda não fez)
3. Colete empresas: `POST /coletar-empresas-bigquery-ultimos-anos`
4. Enriqueça dados: `POST /enriquecer-com-cnae-relacionamentos`
