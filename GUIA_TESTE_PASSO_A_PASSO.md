# 📖 GUIA PASSO A PASSO - SEM CONHECIMENTO DE PROGRAMAÇÃO

## ⚠️ IMPORTANTE
Este é um guia para testar se o sistema está funcionando corretamente após o deploy.

---

## 🎯 O QUE VOCÊ VAI FAZER?

Você vai executar 3 testes:
1. **Teste 1**: Validar se o banco de dados está conectado
2. **Teste 2**: Importar dados de um arquivo Excel
3. **Teste 3**: Confirmar que os dados foram importados com sucesso

---

## 📋 ANTES DE COMEÇAR

Você precisa ter:
- ✅ O arquivo Excel com os dados (ex: `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`)
- ✅ A pasta `comex_data/comexstat_csv/` contendo o arquivo
- ✅ A senha do banco de dados (DATABASE_URL)

---

## 🖥️ PASSO 1: ABRIR O "TERMINAL" (PowerShell)

O "Terminal" é onde você digita comandos para instruir o computador.

### No Windows 10/11:

1. **Clique no botão Iniciar** (logo do Windows no canto inferior esquerdo)
2. **Digite**: `PowerShell`
3. **Clique em**: "Windows PowerShell" (o ícone azul com >_)

Você verá uma janela preta com texto como:
```
PS C:\Users\User>
```

✅ Agora você está no Terminal!

---

## 🖥️ PASSO 2: NAVEGAR ATÉ A PASTA DO PROJETO

Você precisa "entrar" na pasta onde estão os arquivos do projeto.

### Digite isto no PowerShell:
```powershell
cd c:\Users\User\Desktop\Cursor\Projetos\projeto_comex
```

**O que acontece:**
- A pasta que aparece no início muda para `projeto_comex`
- Você vê: `PS C:\Users\User\Desktop\Cursor\Projetos\projeto_comex>`

✅ Pronto! Você está na pasta correta!

---

## 🔑 PASSO 3: CONFIGURAR A SENHA DO BANCO (DATABASE_URL)

Agora você vai "guardar" a senha na memória do terminal, para que os scripts saibam como conectar ao banco.

### Digite isto no PowerShell:
```powershell
$env:DATABASE_URL = "postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb"
```

**O que acontece:**
- Nada visível, mas a senha foi "guardada"
- A senha é usada automaticamente nos próximos comandos

✅ Pronto! A conexão está configurada!

---

## ✅ PASSO 4A: TESTE 1 - VALIDAR O BANCO (RÁPIDO)

Este teste verifica se o sistema consegue conectar ao banco de dados.

### Digite isto no PowerShell:
```powershell
curl -X GET "https://comex-backend-gecp.onrender.com/validar-sistema"
```

**O que esperar:**
- Você verá um resultado como:
```json
{
  "status": "ok",
  "banco_dados": {
    "conectado": true,
    "total_registros": {
      "operacoes": 0,
      "cnae": 0,
      "exportacoes": 0,
      "importacoes": 0
    }
  }
}
```

- Se disser `"status": "ok"` → ✅ Banco está conectado!
- Se disser `"status": "erro"` → ❌ Há um problema com a conexão

---

## 📊 PASSO 4B: TESTE 2 - IMPORTAR DADOS DO EXCEL (MAIS DEMORADO)

Este teste lê o arquivo Excel e coloca os dados no banco.

### Digite isto no PowerShell:
```powershell
python importar_excel_local.py "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
```

**O que esperar:**
- Você verá mensagens como:
```
Lendo arquivo: comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx
Lido 1000 linhas
Inserindo dados em chunks…
Chunk 1: 1000 registros inseridos
✅ Total inserido: 1000 registros
✅ Importação concluída
```

- **Se vir `✅`** → Importação funcionou!
- **Se vir `❌` ou "Erro"** → Há um problema com o arquivo ou banco

---

## 📊 PASSO 4C: TESTE 3 - VALIDAR NOVAMENTE (RÁPIDO)

Este teste confirma que os dados foram salvos.

### Digite isto novamente no PowerShell:
```powershell
curl -X GET "https://comex-backend-gecp.onrender.com/validar-sistema"
```

**O que esperar:**
- Desta vez, você verá os números aumentados:
```json
{
  "status": "ok",
  "banco_dados": {
    "conectado": true,
    "total_registros": {
      "operacoes": 1000,
      "cnae": 0,
      "exportacoes": 500,
      "importacoes": 500
    }
  }
}
```

- ✅ Se o `"operacoes"` for maior que 0, significa que os dados foram importados!

---

## 🚀 PASSO 5: TESTE COMPLETO AUTOMATIZADO (OPCIONAL)

Se você quer fazer tudo isto em um único comando:

### Digite isto no PowerShell:
```powershell
.\test_deploy.ps1 -ServiceUrl "https://comex-backend-gecp.onrender.com" -ExcelPath "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
```

**O que esperar:**
- Vai aguardar 2 minutos (aquecimento do serviço)
- Depois vai fazer os testes 1, 2 e 3 automaticamente
- Você verá mensagens em cores:
  - 🟢 Verde = sucesso
  - 🔴 Vermelho = erro
  - 🟡 Amarelo = aviso

---

## 🐛 SE DER ERRO

### Erro: "File not found"
- **Causa**: O arquivo Excel não está na pasta correta
- **Solução**: Verifique se a pasta `comex_data\comexstat_csv\` existe e tem o arquivo

### Erro: "Connection refused"
- **Causa**: O servidor Render está offline
- **Solução**: Aguarde 5 minutos e tente novamente

### Erro: "401 Unauthorized"
- **Causa**: A senha (DATABASE_URL) está errada
- **Solução**: Copie a senha correta no Render → Environment

### Erro: "Command not found: python"
- **Causa**: Python não está instalado ou configurado
- **Solução**: Instale Python 3.9+ a partir de python.org

---

## 📱 NAVEGADOR WEB (VER RESULTADOS)

Se quiser ver a documentação da API no navegador:

1. **Abra seu navegador** (Chrome, Edge, Firefox, etc.)
2. **Cole na barra de URL**: `https://comex-backend-gecp.onrender.com/docs`
3. **Pressione Enter**

Você verá uma página interativa com todos os endpoints (funções) disponíveis!

---

## 📝 RESUMO DOS COMANDOS

| Passo | O que fazer | Comando |
|-------|------------|---------|
| 1 | Abrir Terminal | Clique Iniciar → PowerShell |
| 2 | Entrar na pasta | `cd c:\Users\User\Desktop\Cursor\Projetos\projeto_comex` |
| 3 | Configurar senha | `$env:DATABASE_URL = "postgresql://..."` |
| 4A | Validar banco | `curl -X GET "https://comex-backend-gecp.onrender.com/validar-sistema"` |
| 4B | Importar Excel | `python importar_excel_local.py "caminho_arquivo.xlsx" --tipo comex` |
| 4C | Validar novamente | `curl -X GET "https://comex-backend-gecp.onrender.com/validar-sistema"` |
| 5 | Teste automático | `.\test_deploy.ps1 -ServiceUrl "..." -ExcelPath "..."` |

---

## ✨ PRÓXIMOS PASSOS

Após os testes darem tudo OK:
1. Faça push das mudanças no Git (se seu time estiver usando)
2. O Render vai fazer deploy automaticamente
3. Acesse o dashboard/frontend para ver os dados

---

## 📞 DÚVIDAS FREQUENTES

**P: Posso fechar o PowerShell depois de um comando?**
R: Não. Deixe aberto para rodar vários comandos. Só feche no final.

**P: Quanto tempo demora cada teste?**
R: Validação: 5 segundos. Importação: 1-5 minutos (depende do arquivo).

**P: Posso importar vários arquivos?**
R: Sim! Repita o comando de importação com o novo caminho do arquivo.

**P: Os dados são apagados quando faço novo deploy?**
R: Não! Os dados ficam salvos no banco PostgreSQL.

---

## 🎉 PRONTO!

Você agora consegue testar o sistema sem conhecimento de programação!

Qualquer dúvida, cole a mensagem de erro aqui e vou ajudar. ✅
