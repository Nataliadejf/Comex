# Como Aprovar Cadastros

## 📧 Email de Notificação

Quando um novo usuário se cadastra, você receberá uma notificação nos **logs do backend** com:

- Email do usuário
- Nome completo
- Token de aprovação
- Link para aprovação

**Exemplo de log:**
```
📧 SOLICITAÇÃO DE APROVAÇÃO DE CADASTRO
Para: nataliadejesus2@gmail.com
Novo usuário solicitou cadastro:
  Nome: João Silva
  Email: joao@exemplo.com
  Token de aprovação: abc123xyz...
Link de aprovação: http://localhost:3000/aprovar?token=abc123xyz...
```

## ✅ Métodos de Aprovação

### Método 1: Via API (Recomendado)

1. Acesse: http://localhost:8000/docs
2. Procure pelo endpoint `POST /aprovar-cadastro`
3. Clique em "Try it out"
4. Cole o token de aprovação do log
5. Clique em "Execute"
6. O cadastro será aprovado automaticamente

### Método 2: Via Script Python

Crie um arquivo `aprovar_cadastro.py`:

```python
import sys
from pathlib import Path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from database.models import Usuario, AprovacaoCadastro
from datetime import datetime

db = next(get_db())

# Buscar cadastro pendente
email = "email_do_usuario@exemplo.com"
usuario = db.query(Usuario).filter(Usuario.email == email).first()

if usuario and usuario.status_aprovacao == "pendente":
    # Aprovar
    usuario.status_aprovacao = "aprovado"
    usuario.ativo = 1
    
    # Atualizar registro de aprovação
    aprovacao = db.query(AprovacaoCadastro).filter(
        AprovacaoCadastro.usuario_id == usuario.id
    ).first()
    if aprovacao:
        aprovacao.status = "aprovado"
        aprovacao.data_aprovacao = datetime.utcnow()
    
    db.commit()
    print(f"✅ Usuário {email} aprovado!")
else:
    print(f"❌ Usuário não encontrado ou já aprovado")
```

### Método 3: Listar Todos os Pendentes

1. Acesse: http://localhost:8000/docs
2. Procure pelo endpoint `GET /cadastros-pendentes`
3. Clique em "Try it out" → "Execute"
4. Você verá uma lista com todos os cadastros pendentes e seus tokens

## 📋 Processo Completo

1. **Usuário se cadastra** → Status: "pendente", Ativo: 0
2. **Você recebe notificação** → Logs do backend mostram token
3. **Você aprova o cadastro** → Via API ou script
4. **Usuário recebe email** → Notificação de cadastro aprovado (log)
5. **Usuário pode fazer login** → Status: "aprovado", Ativo: 1

## 🔍 Verificar Cadastros Pendentes

Para ver todos os cadastros pendentes:

```bash
curl http://localhost:8000/cadastros-pendentes
```

Ou acesse: http://localhost:8000/docs → `GET /cadastros-pendentes`

## ⚠️ Importante

- **Apenas o usuário de teste** (`nataliadejesus2@hotmail.com`) está aprovado automaticamente
- **Todos os outros cadastros** precisam de aprovação manual
- Os tokens de aprovação expiram em **7 dias**
- Após aprovar, o usuário receberá um email (log) informando que pode fazer login

## 📝 Próximos Passos

Para implementar envio real de email:

1. Configure SMTP no `backend/services/email_service.py`
2. Adicione variáveis de ambiente:
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
3. Descomente o código de envio real no arquivo

---

**Email do administrador**: nataliadejesus2@gmail.com
**Última atualização**: 05/01/2026

