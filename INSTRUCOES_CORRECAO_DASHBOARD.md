# 🔧 Instruções para Corrigir o Erro do Dashboard

## ✅ O que foi feito:

1. **Banco de dados recriado** - O banco corrompido foi substituído por um novo
2. **Endpoint corrigido** - Tratamento de erros melhorado
3. **Health check melhorado** - Agora mostra total de registros

## 🔄 Próximo passo: REINICIAR O BACKEND

O backend precisa ser reiniciado para carregar as correções.

### Opção 1: Reiniciar manualmente

1. **Pare o backend atual**:
   - Vá na janela PowerShell onde o backend está rodando
   - Pressione `Ctrl+C` para parar

2. **Inicie novamente**:
   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
   .\venv\Scripts\Activate.ps1
   python run.py
   ```

### Opção 2: Usar nova janela

Abra uma nova janela PowerShell e execute:
```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python run.py
```

## 📊 Depois de reiniciar:

### 1. Verificar se o backend está funcionando:
```bash
# Acesse no navegador:
http://localhost:8000/health

# Deve retornar:
{
  "status": "healthy",
  "database": "connected",
  "total_registros": 0
}
```

### 2. Testar o dashboard:
```bash
# Acesse no navegador:
http://localhost:8000/dashboard/stats?meses=3

# Deve retornar (mesmo sem dados):
{
  "volume_importacoes": 0.0,
  "volume_exportacoes": 0.0,
  "valor_total_usd": 0.0,
  "principais_ncms": [],
  "principais_paises": [],
  "registros_por_mes": {}
}
```

### 3. Se ainda houver erro:

Verifique os logs no console do backend para ver o erro específico.

## 📥 Para ter dados no Dashboard:

O dashboard funcionará, mas mostrará zeros porque não há dados ainda.

Para adicionar dados:

1. **Coloque arquivos CSV em**: `D:\comex\2025\`
   - Exemplo: `EXP_2025.csv`, `IMP_2025.csv`

2. **Processe os arquivos**:
   ```bash
   cd backend
   python scripts/process_single_file.py D:\comex\2025\EXP_2025.csv
   ```

3. **Recarregue o dashboard** no navegador

## ✅ Resumo:

- ✅ Banco recriado
- ✅ Código corrigido  
- ⏳ **PRECISA REINICIAR O BACKEND**
- ⏳ Depois processar dados CSV

**O erro será resolvido após reiniciar o backend!**



