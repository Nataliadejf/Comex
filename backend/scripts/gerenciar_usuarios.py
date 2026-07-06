"""
Gerenciamento de usuários (auth no BigQuery).

Uso (com a chave configurada):
    set GOOGLE_APPLICATION_CREDENTIALS=C:\\Users\\User\\Desktop\\Claude\\liquid-receiver-483923-n6-c1b7eebd2b03.json

    python gerenciar_usuarios.py listar
    python gerenciar_usuarios.py pendentes
    python gerenciar_usuarios.py aprovar  <email>
    python gerenciar_usuarios.py criar    <email> <senha> "<nome completo>"
    python gerenciar_usuarios.py senha     <email> <nova_senha>
    python gerenciar_usuarios.py desativar <email>
    python gerenciar_usuarios.py remover   <email>
"""
import sys
import uuid
from google.cloud import bigquery

try:
    import bcrypt
except ImportError:
    bcrypt = None

T = "liquid-receiver-483923-n6.Projeto_Comex.usuarios"


def _c():
    return bigquery.Client()


def _p(email):
    return [bigquery.ScalarQueryParameter("e", "STRING", (email or "").strip().lower())]


def _hash(senha):
    return bcrypt.hashpw(senha.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def _run(sql, params=None):
    return list(_c().query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params or [])).result())


def listar(apenas_pendentes=False):
    filtro = "WHERE status_aprovacao='pendente' OR ativo=0" if apenas_pendentes else ""
    rows = _run(f"SELECT email,nome_completo,status_aprovacao,ativo,criado_em FROM `{T}` {filtro} ORDER BY criado_em")
    if not rows:
        print("(nenhum usuário)" if not apenas_pendentes else "(nenhum cadastro pendente)")
    for r in rows:
        flag = "✓ ativo" if r.ativo else "⏳ pendente/inativo"
        print(f"  {r.email:40} | {(r.nome_completo or '')[:30]:30} | {flag}")


def aprovar(email):
    _run(f"UPDATE `{T}` SET status_aprovacao='aprovado', ativo=1 WHERE LOWER(email)=@e", _p(email))
    print(f"✅ {email} aprovado — já pode fazer login.")


def desativar(email):
    _run(f"UPDATE `{T}` SET status_aprovacao='inativo', ativo=0 WHERE LOWER(email)=@e", _p(email))
    print(f"⛔ {email} desativado.")


def remover(email):
    _run(f"DELETE FROM `{T}` WHERE LOWER(email)=@e", _p(email))
    print(f"🗑️  {email} removido.")


def redefinir_senha(email, senha):
    p = _p(email) + [bigquery.ScalarQueryParameter("h", "STRING", _hash(senha))]
    _run(f"UPDATE `{T}` SET senha_hash=@h WHERE LOWER(email)=@e", p)
    print(f"🔑 senha de {email} redefinida.")


def criar(email, senha, nome):
    if _run(f"SELECT COUNT(*) n FROM `{T}` WHERE LOWER(email)=@e", _p(email))[0].n:
        print(f"⚠️  {email} já existe. Use 'senha' para redefinir ou 'aprovar'.")
        return
    p = [
        bigquery.ScalarQueryParameter("id", "STRING", str(uuid.uuid4())),
        bigquery.ScalarQueryParameter("e", "STRING", email.strip().lower()),
        bigquery.ScalarQueryParameter("h", "STRING", _hash(senha)),
        bigquery.ScalarQueryParameter("n", "STRING", nome),
    ]
    _run(f"""INSERT INTO `{T}` (id,email,senha_hash,nome_completo,status_aprovacao,ativo,criado_em)
             VALUES (@id,@e,@h,@n,'aprovado',1,CURRENT_TIMESTAMP())""", p)
    print(f"✅ {email} criado e aprovado.")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    cmd = a[0]
    if cmd == "listar":
        listar()
    elif cmd == "pendentes":
        listar(apenas_pendentes=True)
    elif cmd == "aprovar" and len(a) >= 2:
        aprovar(a[1])
    elif cmd == "desativar" and len(a) >= 2:
        desativar(a[1])
    elif cmd == "remover" and len(a) >= 2:
        remover(a[1])
    elif cmd == "senha" and len(a) >= 3:
        redefinir_senha(a[1], a[2])
    elif cmd == "criar" and len(a) >= 4:
        criar(a[1], a[2], a[3])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
