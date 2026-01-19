import os
import json
import tempfile
from contextlib import contextmanager

@contextmanager
def carregar_credenciais_google_temp():
    """
    Context manager que:
    - Lê o JSON da variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS_JSON`
    - Escreve em um arquivo temporário seguro
    - Seta `GOOGLE_APPLICATION_CREDENTIALS` apontando para esse arquivo
    - Remove o arquivo e limpa a variável ao sair do contexto

    Uso:
        with carregar_credenciais_google_temp() as cred_path:
            # bibliotecas Google usam a variável de ambiente aqui
    """
    content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not content:
        raise EnvironmentError("Variável GOOGLE_APPLICATION_CREDENTIALS_JSON não encontrada")

    try:
        creds = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError("Conteúdo de GOOGLE_APPLICATION_CREDENTIALS_JSON inválido") from e

    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(creds, f, ensure_ascii=False)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        yield path
    finally:
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        try:
            os.remove(path)
        except OSError:
            pass
