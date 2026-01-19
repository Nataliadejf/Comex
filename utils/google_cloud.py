import os
import json
import tempfile
import atexit
from contextlib import contextmanager


def _write_creds_temp(creds_dict):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp.write(json.dumps(creds_dict).encode('utf-8'))
    temp.close()
    try:
        os.chmod(temp.name, 0o600)
    except Exception:
        pass
    return temp.name


def carregar_credenciais_google():
    """Compatibilidade simples: escreve o JSON em arquivo temporário,
    seta `GOOGLE_APPLICATION_CREDENTIALS` e registra cleanup no atexit.
    Retorna o caminho do arquivo criado.
    """
    content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not content:
        raise EnvironmentError("Variável GOOGLE_APPLICATION_CREDENTIALS_JSON não encontrada")

    try:
        creds = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError("Conteúdo de GOOGLE_APPLICATION_CREDENTIALS_JSON inválido") from e

    path = _write_creds_temp(creds)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

    def _cleanup():
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        try:
            os.remove(path)
        except OSError:
            pass

    atexit.register(_cleanup)
    return path


@contextmanager
def carregar_credenciais_google_temp():
    """Context manager que cria o arquivo temporário e remove ao sair do contexto."""
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
