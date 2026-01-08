# 📋 Guia de Importação de Dados para PostgreSQL

Este guia explica como importar os dados dos arquivos Excel para o banco PostgreSQL no Render.

## 📁 Arquivos Necessários

Os seguintes arquivos devem estar no diretório `comex_data/comexstat_csv/`:

1. **H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx**
   - Dados de importação e exportação
   - Contém: NCM, Estados, Países, Valores USD, Pesos, etc.

2. **Empresas Importadoras e Exportadoras.xlsx**
   - Lista de empresas
   - Contém: Nome, CNPJ, CNAE, Estado, Valores

## 🚀 Método 1: Via Shell do Render (Recomendado)

### Passo 1: Fazer Upload dos Arquivos

1. No Render Dashboard, vá em **Shell** do serviço backend
2. Execute os seguintes comandos para criar o diretório:

```bash
cd /opt/render/project/src
mkdir -p comex_data/comexstat_csv
```

3. Faça upload dos arquivos Excel usando o método de sua preferência:
   - Via SFTP/SCP
   - Via Git (adicione os arquivos ao repositório)
   - Via Render Dashboard → Manual Deploy (se os arquivos estiverem no Git)

### Passo 2: Executar Importação

```bash
cd /opt/render/project/src/backend
python scripts/import_data.py
```

## 🚀 Método 2: Via Endpoint HTTP (Alternativo)

Se você não tiver acesso ao Shell, pode criar um endpoint temporário protegido por senha.

### Criar Endpoint de Importação

Adicione ao `backend/main.py`:

```python
@app.post("/admin/import-data")
async def importar_dados_admin(
    senha: str = Query(...),
    db: Session = Depends(get_db)
):
    """Endpoint temporário para importar dados."""
    # Proteção simples por senha
    SENHA_ADMIN = os.getenv("ADMIN_PASSWORD", "sua-senha-secreta")
    
    if senha != SENHA_ADMIN:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    try:
        from scripts.import_data import main
        main()
        return {"success": True, "message": "Importação concluída"}
    except Exception as e:
        logger.error(f"Erro na importação: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Executar Importação

```bash
curl -X POST "https://seu-backend.onrender.com/admin/import-data?senha=sua-senha-secreta"
```

## 📊 Verificar Importação

Após a importação, verifique os dados:

```bash
# No Shell do Render
cd /opt/render/project/src/backend
python -c "
from database.database import SessionLocal
from database.models import ComercioExterior, Empresa
db = SessionLocal()
print(f'Registros ComercioExterior: {db.query(ComercioExterior).count()}')
print(f'Empresas: {db.query(Empresa).count()}')
db.close()
"
```

Ou acesse o endpoint:

```
GET https://seu-backend.onrender.com/dashboard/stats?meses=24
```

## ⚠️ Notas Importantes

1. **Tamanho dos Arquivos**: Arquivos Excel grandes podem demorar para importar. O script faz commit a cada 1000 registros para evitar problemas de memória.

2. **Duplicatas**: O script trata duplicatas de empresas (por CNPJ ou nome).

3. **Erros**: Se houver erros, verifique os logs do Render Dashboard.

4. **Performance**: Para arquivos muito grandes, considere dividir em lotes menores.

## 🔧 Troubleshooting

### Erro: "Arquivo não encontrado"

- Verifique se os arquivos estão no caminho correto
- Use caminhos absolutos se necessário

### Erro: "Connection timeout"

- Aumente o timeout do PostgreSQL no Render
- Divida a importação em lotes menores

### Erro: "Memory error"

- O script já faz commit periódico, mas se ainda houver problemas, reduza o tamanho do lote

## 📝 Estrutura das Tabelas

### `comercio_exterior`
- Armazena dados de importação/exportação
- Campos principais: tipo, ncm, estado, pais, valor_usd, peso_kg, data

### `empresas`
- Armazena informações de empresas
- Campos principais: nome, cnpj, cnae, estado, tipo, valor_importacao, valor_exportacao

### `cnae_hierarquia`
- Armazena hierarquia CNAE (opcional)
- Campos principais: cnae, descricao, setor, segmento, ramo, categoria
