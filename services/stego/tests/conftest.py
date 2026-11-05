"""Configuración mínima para importar la aplicación sin Docker secrets."""
import hashlib
import os
import tempfile
from pathlib import Path


_secrets = Path(tempfile.mkdtemp(prefix="stego-test-secrets-"))
(_secrets / "svc_hash_gateway").write_text(
    hashlib.sha256(b"token-de-prueba-gateway").hexdigest(), encoding="utf-8"
)
os.environ.setdefault("SECRETS_DIR", str(_secrets))
