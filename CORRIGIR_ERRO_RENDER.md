# 🔧 Corrigir Erro no Render - "maturin failed"

## ❌ Erro Encontrado

O erro mostra:
- `maturin failed` (ferramenta Rust)
- `Read-only file system`
- `Preparing metadata (pyproject.toml): finished with status 'error'`

## 🔍 Causa do Problema

O Render está tentando compilar dependências que requerem Rust, mas está falhando. Isso geralmente acontece quando:
1. Alguma dependência no `requirements.txt` requer compilação Rust
2. O Render está usando configuração incorreta

## ✅ SOLUÇÃO

### Opção 1: Usar requirements-render.txt (RECOMENDADO)

1. No Render, vá em **Settings** do seu serviço
2. Role até **Build & Deploy**
3. Encontre **Build Command**
4. Mude de:
   ```
   pip install -r requirements.txt
   ```
   Para:
   ```
   pip install -r requirements-render.txt
   ```
5. Clique em **Save Changes**
6. O serviço vai reiniciar automaticamente

### Opção 2: Atualizar requirements.txt

Se preferir manter um único arquivo, edite `requirements.txt` e remova dependências problemáticas.

### Opção 3: Verificar Configuração

Certifique-se de que:
- ✅ **Runtime**: Python 3 (NÃO Docker)
- ✅ **Root Directory**: `backend`
- ✅ **Build Command**: `pip install -r requirements-render.txt`

## 📋 Dependências Removidas (temporariamente)

As seguintes dependências foram removidas do `requirements-render.txt`:
- `pandas` (muito pesada, requer muitas dependências)
- `numpy` (dependência pesada)
- `selenium` (não essencial para API)
- `openpyxl` (pode ser adicionado depois se necessário)

## 🚀 Próximos Passos

1. Atualize o Build Command no Render
2. Aguarde o novo deploy
3. Se ainda der erro, verifique os logs para ver qual dependência está causando problema

## 💡 Dica

Se precisar de alguma dependência removida depois:
- Adicione uma por vez
- Teste o deploy
- Se funcionar, adicione a próxima

