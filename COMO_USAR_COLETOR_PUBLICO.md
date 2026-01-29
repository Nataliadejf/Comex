# Como Usar o Coletor de Dados Públicos

## 📋 Problemas Corrigidos

1. ✅ **Erro `bs4` não encontrado**: BeautifulSoup agora é importado opcionalmente
2. ✅ **Coleta DOU melhorada**: Busca em múltiplas páginas e termos
3. ✅ **Scripts standalone**: Para executar localmente sem depender do endpoint

## 🚀 Opções de Execução

### Opção 1: Via Endpoint API (Render)

Após o deploy, use o endpoint:

```bash
POST /api/coletar-dados-publicos
{
  "limite_por_fonte": 50000,
  "integrar_banco": true,
  "salvar_csv": true
}
```

### Opção 2: Script Standalone (Recomendado)

Execute diretamente no terminal:

```bash
# Coletar todas as fontes (50k registros)
python coletar_dados_publicos_standalone.py

# Coletar apenas DOU
python coletar_dados_publicos_standalone.py --apenas-dou --limite 10000

# Coletar apenas BigQuery
python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 50000

# Salvar em CSV
python coletar_dados_publicos_standalone.py --salvar-csv

# Salvar em JSON
python coletar_dados_publicos_standalone.py --salvar-json

# Todas as opções
python coletar_dados_publicos_standalone.py --limite 50000 --salvar-csv --salvar-json --integrar-banco
```

### Opção 3: Validar BigQuery Primeiro

Antes de coletar, valide a conexão:

```bash
python validar_bigquery.py
```

Isso vai:
- ✅ Verificar conexão BigQuery
- ✅ Listar todas as tabelas disponíveis
- ✅ Testar queries nas tabelas principais
- ✅ Mostrar quantos registros existem

## 📊 Tabelas BigQuery Esperadas

Baseado na sua imagem do Google Cloud, estas tabelas devem estar disponíveis:

- `NCMExportacao`
- `EmpresasImEx`
- `EmpresasMes7_2025`
- `Estabelecimentoscnpj`
- `municipio_exportacao`
- `municipio_importacao`
- `NCMImportacao`

## 🔧 Requisitos

1. **Dependências instaladas**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Variáveis de ambiente** (para BigQuery):
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Credenciais do Google Cloud (JSON string)

3. **Banco de dados** (opcional, se `--integrar-banco`):
   - `DATABASE_URL`: URL de conexão PostgreSQL

## 📝 Logs

Os scripts geram logs automáticos:
- Console: Saída em tempo real
- Arquivo: `coleta_publica_YYYYMMDD_HHMMSS.log`

## ⚠️ Troubleshooting

### Erro: "No module named 'bs4'"
```bash
pip install beautifulsoup4
```

### Erro: "GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada"
Configure a variável de ambiente ou use apenas `--apenas-dou`

### Erro: "PublicCompanyCollector não está disponível"
Verifique os logs do servidor Render ou execute o script standalone localmente

## 🔗 Cruzamento NCM + UF (após coleta)

Após os dados estarem no banco, o sistema pode executar o **cruzamento** entre:
- Empresas **importadoras** e **exportadoras**
- Por **NCM** e **UF** (município/estado)
- Resultados salvos na tabela `empresas_recomendadas`

### Via API
- **POST /api/coletar-dados-publicos** com `"executar_cruzamento": true` (padrão) — coleta e depois cruza.
- **POST /api/cruzamento-ncm-uf** — executa apenas o cruzamento (dados já no banco).

### Via script
```bash
python coletar_dados_publicos_standalone.py --limite 5000 --integrar-banco --executar-cruzamento
```

## 🎯 Próximos Passos

1. **Validar BigQuery**: Execute `python validar_bigquery.py`
2. **Testar coleta local**: Execute `python coletar_dados_publicos_standalone.py --limite 1000 --salvar-csv`
3. **Aguardar deploy**: Após deploy no Render, testar endpoint
4. **Coleta completa**: Executar com `--limite 50000` e `--executar-cruzamento` para coleta + cruzamento
