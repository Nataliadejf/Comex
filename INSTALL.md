# Guia de Instalação - Comex Analyzer

## Pré-requisitos

### Backend (Python)
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Frontend (Node.js)
- Node.js 18.x ou superior
- npm ou yarn

### Opcional (para scraping)
- Google Chrome ou Chromium instalado
- ChromeDriver (será baixado automaticamente pelo Selenium)

## Instalação do Backend

1. **Navegar para o diretório do backend:**
```bash
cd comex_analyzer/backend
```

2. **Criar ambiente virtual:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

4. **Configurar variáveis de ambiente:**
```bash
# Copiar arquivo de exemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

5. **Editar arquivo .env:**
   - Ajustar `DATA_DIR` se necessário (padrão: `D:\comex_data`)
   - Configurar `COMEX_STAT_API_URL` e `COMEX_STAT_API_KEY` se disponível

6. **Inicializar banco de dados:**
```bash
python -c "from database import init_db; init_db()"
```

## Instalação do Frontend

1. **Navegar para o diretório do frontend:**
```bash
cd comex_analyzer/frontend
```

2. **Instalar dependências:**
```bash
npm install
```

3. **Configurar URL da API (opcional):**
   - Criar arquivo `.env` na pasta `frontend`
   - Adicionar: `REACT_APP_API_URL=http://localhost:8000`

## Executando a Aplicação

### Backend

```bash
cd comex_analyzer/backend
python main.py
```

O servidor estará disponível em: `http://localhost:8000`

Documentação da API: `http://localhost:8000/docs`

### Frontend (Modo Desenvolvimento)

**Opção 1: React apenas (para desenvolvimento web)**
```bash
cd comex_analyzer/frontend
npm start
```

**Opção 2: Electron (aplicação desktop)**
```bash
cd comex_analyzer/frontend
npm run dev
```

### Frontend (Modo Produção)

1. **Build do React:**
```bash
cd comex_analyzer/frontend
npm run build
```

2. **Executar Electron:**
```bash
npm run electron
```

3. **Gerar executável:**
```bash
npm run electron-build
```

## Estrutura de Diretórios de Dados

O sistema criará automaticamente a seguinte estrutura em `D:\comex_data\`:

```
D:\comex_data\
├── raw\                    # Dados brutos baixados
│   ├── 2024-11\
│   ├── 2024-12\
│   └── 2025-01\
├── processed\              # Dados processados
├── database\               # Banco de dados SQLite
│   └── comex.db
├── exports\                # Relatórios exportados
└── logs\                   # Logs do sistema
```

## Primeiros Passos

1. **Iniciar o backend:**
   ```bash
   cd comex_analyzer/backend
   python main.py
   ```

2. **Coletar dados iniciais:**
   - Acessar `http://localhost:8000/docs`
   - Executar endpoint `POST /coletar-dados`
   - Ou usar o botão "Coletar Dados" no frontend

3. **Acessar o frontend:**
   - Abrir `http://localhost:3000` (modo web)
   - Ou executar `npm run electron` (modo desktop)

## Solução de Problemas

### Erro: "ModuleNotFoundError"
- Verificar se o ambiente virtual está ativado
- Reinstalar dependências: `pip install -r requirements.txt`

### Erro: "Port already in use"
- Backend: Alterar porta no arquivo `main.py` ou variável de ambiente
- Frontend: Fechar outras instâncias do React ou alterar porta

### Erro: "ChromeDriver not found"
- Instalar Chrome/Chromium
- O Selenium tentará baixar o ChromeDriver automaticamente

### Banco de dados não inicializa
- Verificar permissões de escrita no diretório `D:\comex_data\database\`
- Verificar se o SQLite está funcionando: `python -c "import sqlite3; print('OK')"`

## Suporte

Para mais informações, consulte o arquivo `README.md` na raiz do projeto.

