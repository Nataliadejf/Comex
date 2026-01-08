# 🚀 Como Executar Análise SEM Shell do Render

Como você não tem acesso ao Shell do Render (requer plano pago), criamos **endpoints na API** para executar a análise via HTTP.

## 📋 Endpoints Disponíveis

### 1. Verificar Dados no Banco

**GET** `https://comex-backend-wjco.onrender.com/api/analise/verificar-dados`

Retorna contagem de registros em todas as tabelas:
- `operacoes_comex`
- `comercio_exterior`
- `empresas`
- `empresas_recomendadas`

**Exemplo de resposta:**
```json
{
  "operacoes_comex": {
    "total": 500,
    "importacoes": 250,
    "exportacoes": 250
  },
  "comercio_exterior": {
    "total": 1000,
    "importacoes": 500,
    "exportacoes": 500
  },
  "empresas": {
    "total": 50
  },
  "empresas_recomendadas": {
    "total": 0,
    "provaveis_importadoras": 0,
    "provaveis_exportadoras": 0
  }
}
```

### 2. Verificar Status da Análise

**GET** `https://comex-backend-wjco.onrender.com/api/analise/status-analise`

Verifica se a análise já foi executada e quantas empresas foram encontradas.

**Exemplo de resposta:**
```json
{
  "status": "nao_executada",
  "message": "Análise ainda não foi executada",
  "total_empresas": 0
}
```

### 3. Executar Análise

**POST** `https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas`

Executa a análise completa e cria a tabela `empresas_recomendadas`.

**⚠️ IMPORTANTE:** Esta operação pode demorar alguns minutos!

**Exemplo de resposta:**
```json
{
  "success": true,
  "message": "Análise executada com sucesso",
  "total_empresas": 150,
  "provaveis_importadoras": 80,
  "provaveis_exportadoras": 70
}
```

## 🎯 Como Usar

### Opção 1: Via Navegador (GET apenas)

1. **Verificar dados:**
   ```
   https://comex-backend-wjco.onrender.com/api/analise/verificar-dados
   ```

2. **Verificar status:**
   ```
   https://comex-backend-wjco.onrender.com/api/analise/status-analise
   ```

### Opção 2: Via cURL (Terminal)

1. **Verificar dados:**
   ```bash
   curl https://comex-backend-wjco.onrender.com/api/analise/verificar-dados
   ```

2. **Verificar status:**
   ```bash
   curl https://comex-backend-wjco.onrender.com/api/analise/status-analise
   ```

3. **Executar análise:**
   ```bash
   curl -X POST https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas
   ```

### Opção 3: Via PowerShell (Windows)

1. **Verificar dados:**
   ```powershell
   Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/verificar-dados" -Method Get
   ```

2. **Verificar status:**
   ```powershell
   Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/status-analise" -Method Get
   ```

3. **Executar análise:**
   ```powershell
   Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas" -Method Post
   ```

### Opção 4: Via Postman ou Insomnia

1. **Verificar dados:**
   - Método: `GET`
   - URL: `https://comex-backend-wjco.onrender.com/api/analise/verificar-dados`

2. **Verificar status:**
   - Método: `GET`
   - URL: `https://comex-backend-wjco.onrender.com/api/analise/status-analise`

3. **Executar análise:**
   - Método: `POST`
   - URL: `https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas`

## 📝 Fluxo Recomendado

1. **Verificar se há dados:**
   ```
   GET /api/analise/verificar-dados
   ```
   
   Se `comercio_exterior.total` ou `operacoes_comex.total` > 0, continue.

2. **Verificar status da análise:**
   ```
   GET /api/analise/status-analise
   ```
   
   Se `status` = `"nao_executada"`, execute a análise.

3. **Executar análise:**
   ```
   POST /api/analise/executar-analise-empresas
   ```
   
   ⚠️ Aguarde alguns minutos (pode demorar para grandes volumes de dados).

4. **Verificar resultado:**
   ```
   GET /api/analise/status-analise
   ```
   
   Deve retornar `status: "executada"` e `total_empresas > 0`.

5. **Testar dashboard:**
   ```
   https://comex-4.onrender.com
   ```
   
   O dashboard deve mostrar dados das empresas recomendadas.

## ⚠️ Importante

- A análise pode demorar **vários minutos** dependendo do volume de dados
- Não feche a janela/tab enquanto a análise estiver rodando
- Se der timeout, tente novamente (a análise pode ter completado mesmo assim)
- Verifique os logs do backend no Render Dashboard para acompanhar o progresso

## 🐛 Troubleshooting

### Erro: "Tabela não existe"

A tabela será criada automaticamente na primeira execução. Se der erro, verifique se o modelo está correto.

### Erro: "Nenhum dado encontrado"

Execute primeiro a importação de dados:
- Certifique-se de que os arquivos Excel estão em `backend/data/`
- Ou execute a importação via endpoint (se disponível)

### Timeout na requisição

- A análise pode estar rodando em background
- Verifique o status após alguns minutos
- Verifique os logs do backend no Render

## 📊 Exemplo Completo (PowerShell)

```powershell
# 1. Verificar dados
Write-Host "Verificando dados..." -ForegroundColor Cyan
$dados = Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/verificar-dados"
Write-Host "OperacoesComex: $($dados.operacoes_comex.total)" -ForegroundColor Green
Write-Host "ComercioExterior: $($dados.comercio_exterior.total)" -ForegroundColor Green
Write-Host "Empresas: $($dados.empresas.total)" -ForegroundColor Green

# 2. Verificar status
Write-Host "`nVerificando status da análise..." -ForegroundColor Cyan
$status = Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/status-analise"
Write-Host "Status: $($status.status)" -ForegroundColor Yellow

# 3. Se não executada, executar análise
if ($status.status -eq "nao_executada") {
    Write-Host "`nExecutando análise (pode demorar alguns minutos)..." -ForegroundColor Yellow
    $resultado = Invoke-RestMethod -Uri "https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas" -Method Post
    Write-Host "✅ Análise concluída!" -ForegroundColor Green
    Write-Host "Total de empresas: $($resultado.total_empresas)" -ForegroundColor Green
    Write-Host "Prováveis importadoras: $($resultado.provaveis_importadoras)" -ForegroundColor Green
    Write-Host "Prováveis exportadoras: $($resultado.provaveis_exportadoras)" -ForegroundColor Green
} else {
    Write-Host "`nAnálise já foi executada!" -ForegroundColor Green
    Write-Host "Total de empresas: $($status.total_empresas)" -ForegroundColor Green
}
```
