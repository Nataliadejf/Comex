# Guia Rápido - Comex Analyzer

## 🚀 Início Rápido (5 minutos)

### 1. Backend

```bash
# Navegar para o backend
cd comex_analyzer/backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar (copiar .env.example para .env e ajustar se necessário)
# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env

# Iniciar servidor
python run.py
```

O backend estará rodando em: `http://localhost:8000`

### 2. Frontend

```bash
# Em outro terminal, navegar para o frontend
cd comex_analyzer/frontend

# Instalar dependências
npm install

# Iniciar aplicação (modo desenvolvimento)
npm start
```

Para modo Electron (desktop):
```bash
npm run dev
```

### 3. Primeira Coleta de Dados

1. Abra o navegador em `http://localhost:3000` (ou use o Electron)
2. Clique no botão **"Coletar Dados"** no header
3. Aguarde a coleta concluir (pode levar alguns minutos)
4. Visualize os dados no Dashboard

## 📊 Funcionalidades Principais

### Dashboard
- Métricas principais (volumes, valores)
- Gráficos interativos
- Top NCMs e países

### Busca Avançada
- Filtros múltiplos
- Paginação
- Exportação de resultados

### Análise por NCM
- Estatísticas detalhadas
- Evolução temporal
- Principais países

## 🔧 Configuração Rápida

### Alterar Diretório de Dados

Edite `backend/.env`:
```env
DATA_DIR=C:\meu_caminho\comex_data
```

### Alterar Porta do Backend

Edite `backend/run.py`:
```python
uvicorn.run(..., port=8001)
```

### Alterar URL da API no Frontend

Crie `frontend/.env`:
```env
REACT_APP_API_URL=http://localhost:8000
```

## 📝 Próximos Passos

1. **Coletar dados**: Use o botão "Coletar Dados" para popular o banco
2. **Explorar Dashboard**: Veja as métricas e gráficos
3. **Fazer buscas**: Use a busca avançada para filtrar dados
4. **Analisar NCMs**: Digite um código NCM para análise detalhada
5. **Exportar relatórios**: Use a funcionalidade de exportação

## ❓ Problemas Comuns

### Backend não inicia
- Verifique se Python 3.11+ está instalado
- Verifique se todas as dependências foram instaladas
- Verifique se a porta 8000 está livre

### Frontend não conecta ao backend
- Verifique se o backend está rodando
- Verifique a URL da API no `.env` do frontend
- Verifique o CORS no backend

### Erro ao coletar dados
- Verifique conexão com internet
- Verifique se o Portal Comex Stat está acessível
- Verifique os logs em `D:\comex_data\logs\`

## 📚 Documentação Completa

- **Instalação detalhada**: Veja `INSTALL.md`
- **API**: Veja `docs/API.md`
- **Arquitetura**: Veja `docs/ARQUITETURA.md`

## 🆘 Suporte

Para mais informações, consulte a documentação completa ou os logs do sistema.

