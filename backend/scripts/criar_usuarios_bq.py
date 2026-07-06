"""
Cria a tabela `usuarios` no BigQuery (auth migrada do Postgres) e recria o
usuário administrador aprovado.

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<chave>
    python criar_usuarios_bq.py <email> <senha> "<nome completo>"
"""
import sys
import uuid
from datetime import datetime
from google.cloud import bigquery

try:
    import bcrypt
except ImportError:
    bcrypt = None

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
TBL = f"{PROJ}.usuarios"


def hash_senha(senha: str) -> str:
    s = senha.encode("utf-8")[:72]
    return bcrypt.hashpw(s, bcrypt.gensalt()).decode("utf-8")


def main():
    c = bigquery.Client()
    print(f"Projeto: {c.project}")

    # 1) Tabela
    c.query(f"""
    CREATE TABLE IF NOT EXISTS `{TBL}` (
      id STRING, email STRING, senha_hash STRING, nome_completo STRING,
      nome_empresa STRING, cpf STRING, cnpj STRING, data_nascimento DATE,
      status_aprovacao STRING, ativo INT64,
      criado_em TIMESTAMP, ultimo_login TIMESTAMP
    )
    """).result()
    print(f"OK - tabela {TBL}")

    # 2) Usuário admin (aprovado)
    email = (sys.argv[1] if len(sys.argv) > 1 else "nataliadejesus2@hotmail.com").strip().lower()
    senha = sys.argv[2] if len(sys.argv) > 2 else "senha123"
    nome = sys.argv[3] if len(sys.argv) > 3 else "Natália de Jesus França França"

    existe = list(c.query(
        f"SELECT COUNT(*) n FROM `{TBL}` WHERE LOWER(email)=@e",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("e", "STRING", email)]),
    ).result())[0].n
    if existe:
        # atualiza senha e reativa
        c.query(
            f"UPDATE `{TBL}` SET senha_hash=@h, ativo=1, status_aprovacao='aprovado' WHERE LOWER(email)=@e",
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("h", "STRING", hash_senha(senha)),
                bigquery.ScalarQueryParameter("e", "STRING", email)]),
        ).result()
        print(f"Usuário {email} já existia — senha redefinida e reativado.")
    else:
        c.query(
            f"""INSERT INTO `{TBL}` (id,email,senha_hash,nome_completo,status_aprovacao,ativo,criado_em)
                VALUES (@id,@e,@h,@n,'aprovado',1,CURRENT_TIMESTAMP())""",
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("id", "STRING", str(uuid.uuid4())),
                bigquery.ScalarQueryParameter("e", "STRING", email),
                bigquery.ScalarQueryParameter("h", "STRING", hash_senha(senha)),
                bigquery.ScalarQueryParameter("n", "STRING", nome)]),
        ).result()
        print(f"Usuário {email} criado e aprovado.")

    n = list(c.query(f"SELECT COUNT(*) n FROM `{TBL}`").result())[0].n
    print(f"Total de usuários: {n}")


if __name__ == "__main__":
    main()
