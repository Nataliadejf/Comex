"""Decodifica GOOGLE_APPLICATION_CREDENTIALS_JSON (base64 ou JSON puro) antes do uvicorn."""
from __future__ import annotations

import base64
import json
import os
import tempfile


def setup_gcp_credentials() -> None:
    raw = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or "").strip()
    if not raw:
        return
    try:
        if raw.startswith("{"):
            creds_json = raw
        else:
            creds_json = base64.b64decode(raw).decode("utf-8")
        json.loads(creds_json)
    except Exception:
        creds_json = raw
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8")
    tmp.write(creds_json)
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name


if __name__ == "__main__":
    setup_gcp_credentials()
