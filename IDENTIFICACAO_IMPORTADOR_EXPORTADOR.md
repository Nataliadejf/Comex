# 📊 Identificação de Importador/Exportador

## ✅ Implementação

### Campos Adicionados ao Banco:

1. **`is_importacao`** (VARCHAR(1))
   - `'S'` = Sim, é importação
   - `'N'` = Não, não é importação
   - Índice criado para consultas rápidas

2. **`is_exportacao`** (VARCHAR(1))
   - `'S'` = Sim, é exportação
   - `'N'` = Não, não é exportação
   - Índice criado para consultas rápidas

### Campo Existente Mantido:

- **`tipo_operacao`** (ENUM)
   - `'Importação'` ou `'Exportação'`
   - Mantido para compatibilidade

## 🔍 Como Usar:

### Consultas SQL:

```sql
-- Buscar apenas importações
SELECT * FROM operacoes_comex WHERE is_importacao = 'S';

-- Buscar apenas exportações
SELECT * FROM operacoes_comex WHERE is_exportacao = 'S';

-- Contar importações e exportações
SELECT 
    COUNT(*) FILTER (WHERE is_importacao = 'S') as total_importacoes,
    COUNT(*) FILTER (WHERE is_exportacao = 'S') as total_exportacoes
FROM operacoes_comex;
```

### Via API:

```python
# Os campos estão disponíveis na resposta:
{
    "id": 1,
    "ncm": "12345678",
    "tipo_operacao": "Importação",
    "is_importacao": "S",
    "is_exportacao": "N",
    ...
}
```

## 📋 Script de Migração:

Execute para adicionar os campos ao banco existente:

```bash
cd backend
python scripts/adicionar_campos_importador_exportador.py
```

Este script:
- ✅ Adiciona as colunas se não existirem
- ✅ Cria índices para performance
- ✅ Atualiza registros existentes baseado em `tipo_operacao`

## 🎯 Vantagens:

1. **Consultas mais rápidas**: Índices específicos
2. **Identificação clara**: Campos booleanos explícitos
3. **Compatibilidade**: Mantém campo `tipo_operacao` existente
4. **Filtros fáceis**: `WHERE is_importacao = 'S'` é mais claro

## ✅ Status:

- ✅ Campos adicionados ao modelo
- ✅ Transformer atualizado para preencher campos
- ✅ Script de migração criado
- ✅ API retorna os novos campos
- ⏳ Execute o script de migração para atualizar banco existente



