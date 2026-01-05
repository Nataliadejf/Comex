# Como Verificar Logs do Deploy no Render

## 🔍 Passo a Passo para Ver os Logs

### PASSO 1: Acessar os Logs

1. **No Render Dashboard:**
   - Clique no serviço `comex-backend`
   - No menu lateral esquerdo, clique em **"Logs"**
   - Ou clique no evento com erro (o que tem o X vermelho)

### PASSO 2: Ver Logs do Build

1. **Nos Logs, procure por:**
   - Mensagens que começam com `==>` (indicam etapas do build)
   - Mensagens em vermelho ou com "Error", "Failed", "Exception"
   - A última mensagem antes do erro

2. **Copie a mensagem de erro completa** e me envie

### PASSO 3: Erros Comuns nos Logs

#### Erro: "No such file or directory: requirements-render-ultra-minimal.txt"
**Causa:** Arquivo não encontrado
**Solução:** Verificar se o arquivo existe em `backend/requirements-render-ultra-minimal.txt`

#### Erro: "ERROR: Could not find a version that satisfies the requirement"
**Causa:** Dependência não encontrada ou versão inválida
**Solução:** Verificar versões das dependências no arquivo

#### Erro: "ModuleNotFoundError" ou "ImportError"
**Causa:** Módulo Python não encontrado após instalação
**Solução:** Adicionar dependência faltante

#### Erro: "Failed building wheel" ou "maturin failed"
**Causa:** Tentativa de compilar código Rust/C
**Solução:** Usar apenas pacotes pré-compilados (`--only-binary :all:`)

#### Erro: "Command failed" ou "Exited with status 1"
**Causa:** Erro genérico no build
**Solução:** Verificar mensagens anteriores nos logs

## 📋 O que Copiar dos Logs

Quando verificar os logs, copie:

1. **As últimas 20-30 linhas** dos logs
2. **Especialmente:**
   - Linhas que começam com `ERROR:`
   - Linhas que começam com `==>`
   - Mensagens em vermelho
   - A última mensagem antes de "Exited with status 1"

## 🎯 Enviar os Logs

Após copiar os logs:

1. Cole aqui no chat
2. Ou me diga qual é a mensagem de erro principal
3. Vou ajudar a corrigir o problema

---

**Última atualização**: 05/01/2026

