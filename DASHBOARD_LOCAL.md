# Dashboard local – como subir

## Opção 1: Um comando (backend + frontend)

Na pasta **projeto_comex** (raiz do projeto):

```powershell
.\SubirDashboardLocalCompleto.ps1
```

- Abre uma **nova janela** com o backend (porta 8000).
- Neste terminal sobe o frontend (porta 3000).
- Acesse: **http://localhost:3000/dashboard**

Se estiver dentro de `backend\`, antes execute: `cd ..`

---

## Opção 2: Dois terminais

**Terminal 1 – Backend**

Na pasta **projeto_comex**:

```powershell
.\SubirDashboardLocal.ps1
```

(Se estiver em `backend\`: `cd ..` e depois `.\SubirDashboardLocal.ps1`)

**Terminal 2 – Frontend**

```powershell
cd frontend
npm start
```

Depois acesse: **http://localhost:3000/dashboard**

---

## Configuração

- **Backend:** porta **8000** (ou `$env:PORT=8001` se 8000 estiver em uso).
- **Frontend:** usa `frontend\.env.development` → `REACT_APP_API_URL=http://localhost:8000`.
- Se o backend estiver na 8001, altere em `.env.development` para `http://localhost:8001`.

---

## Banco de dados local

- Caminho: `projeto_comex\comex_data\database\comex.db` (SQLite).
- O script cria `comex_data\database\` se não existir.
- Se o banco estiver vazio, o dashboard abre com cards zerados; é preciso importar dados (Excel/API) para ver valores.

---

## Se não funcionar

1. **Backend não inicia**
   - Na pasta `projeto_comex\backend`: `pip install -r requirements.txt`
   - Conferir se a porta 8000 está livre.

2. **Frontend não conecta no backend**
   - Verificar `frontend\.env.development`: `REACT_APP_API_URL=http://localhost:8000`
   - Testar no navegador: http://localhost:8000/health (deve retornar JSON com `"status": "healthy"`).

3. **Dashboard em branco ou erro**
   - Abrir o console do navegador (F12) e ver a URL das requisições e possíveis erros.
   - Backend com dados: http://localhost:8000/docs para testar o endpoint `/dashboard/stats`.
