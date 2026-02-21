# Como conectar o Dashboard local

O erro **"Connection Failed" / ERR_CONNECTION_REFUSED** aparece quando o **frontend** (React) ou o **backend** (FastAPI) não estão rodando. É preciso ter **os dois** ativos ao mesmo tempo.

## Opção 1: Usar o arquivo .bat (recomendado)

1. No Explorador de Arquivos, vá até a pasta do projeto:  
   `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex`

2. Dê **dois cliques** em **`SubirDashboardLocal.bat`**.

3. Vão abrir **duas janelas pretas (CMD)**:
   - **Comex Backend**: deve aparecer algo como `Uvicorn running on http://0.0.0.0:8000`  
     → **Não feche essa janela.**
   - **Comex Frontend**: o React vai subir e pode abrir o navegador sozinho em alguns segundos.  
     → **Não feche essa janela.**

4. No navegador, acesse:  
   **http://localhost:3000/dashboard**

5. Se você usa o **Electron** (app “Restart Browser”):  
   - Só abra o Electron **depois** que as duas janelas estiverem abertas e o backend mostrar "Uvicorn running".  
   - Se ainda aparecer "Connection Failed", espere 1–2 minutos e clique em **"Restart Browser"**.

---

## Opção 2: PowerShell (script completo)

1. Abra o **PowerShell** (não precisa ser Administrador).

2. Vá para a pasta do projeto:
   ```powershell
   cd "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex"
   ```

3. Se aparecer erro de política de execução, rode uma vez:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

4. Execute o script:
   ```powershell
   .\SubirDashboardLocalCompleto.ps1
   ```

5. Vai abrir **uma nova janela** com o backend; nesta janela vai subir o frontend. Quando terminar de compilar, acesse:  
   **http://localhost:3000/dashboard**

---

## Opção 3: Manual (duas abas/terminais)

### Terminal 1 – Backend

```powershell
cd "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend"
$env:PORT="8000"
python run.py
```

Deixe rodando até aparecer algo como: `Uvicorn running on http://0.0.0.0:8000`.

### Terminal 2 – Frontend

Abra **outro** PowerShell ou CMD e rode:

```powershell
cd "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\frontend"
npm start
```

Quando abrir o navegador ou quando estiver pronto, acesse:  
**http://localhost:3000/dashboard**

---

## Conferir se está tudo certo

| O que verificar | Onde |
|------------------|------|
| Backend rodando  | Janela com "Uvicorn running on http://0.0.0.0:8000" |
| Frontend rodando | Janela com "webpack compiled" / "Compiled successfully" |
| Dashboard        | Navegador em **http://localhost:3000/dashboard** |

Se o frontend não abrir o navegador sozinho, abra o Chrome ou Edge e digite: **http://localhost:3000/dashboard**.

---

## Erros comuns

- **"Connection Refused"**  
  Backend ou frontend não está rodando. Confira se as duas janelas (backend e frontend) estão abertas e sem mensagem de erro.

- **"python não é reconhecido"**  
  Instale o Python e marque a opção "Add Python to PATH", ou use o caminho completo do `python.exe` no comando.

- **"npm não é reconhecido"**  
  Instale o Node.js (nodejs.org) e feche e abra o terminal de novo.

- **Porta 3000 ou 8000 em uso**  
  Feche outros programas que usem essa porta ou reinicie o PC e rode de novo o `.bat` ou o script.
