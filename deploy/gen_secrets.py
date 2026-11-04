"""Genera los secretos de deploy/secrets/ (spec §11.1).

Nunca sobrescribe un secreto existente; --rotate NOMBRE regenera uno (y lo que se deriva de él).
Uso:  python deploy/gen_secrets.py [--rotate NOMBRE] [--dir RUTA]
Requiere `cryptography` (incluido en el .venv del proyecto).
"""

import argparse
import hashlib
import os
import secrets
from collections.abc import Callable
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SERVICES = ("auth",)  # los que tienen BD (stego no)
CALLERS = ("gateway",)  # quienes llaman a los servicios; en el primer parcial, solo el gateway
RANDOM = (
    "postgres_password",
    *(f"db_{svc}_{role}" for svc in SERVICES for role in ("owner", "app")),
    *(f"svc_token_{caller}" for caller in CALLERS),
)
# Las contraseñas de BD no se rotan aquí: Postgres solo las lee al crear el volumen; cambiarlas
# requiere ALTER ROLE ... PASSWORD en la BD y luego el archivo.
ROTATABLE = (*(f"svc_token_{caller}" for caller in CALLERS), "jwt_signing_key")


def new_jwt_key() -> str:
    """RSA de 3072 bits para los JWT RS256 de auth (spec §11.1)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


class Generator:
    def __init__(self, root: Path, rotate: str | None) -> None:
        self.secrets_dir = root / "secrets"
        self.rotate = rotate

    def path(self, name: str) -> Path:
        return self.secrets_dir / name

    def read(self, name: str) -> str:
        return self.path(name).read_text(encoding="utf-8").strip()

    def write(self, name: str, content: str) -> None:
        """Atómica (temporal + os.replace) y con LF: los secretos se montan en contenedores Linux."""
        path = self.path(name)
        tmp = path.with_name(f".{name}.tmp")
        tmp.write_text(content, encoding="utf-8", newline="\n")
        # legible por el uid 10001 del contenedor; el directorio es 0700 (spec §11.1)
        tmp.chmod(0o644)
        os.replace(tmp, path)
        print(f"generado: {name}")

    def ensure(self, name: str, make: Callable[[], str]) -> None:
        if self.rotate == name or not self.path(name).exists():
            self.write(name, make())

    def derive(self, name: str, content: str) -> None:
        """Lo derivado de un token se recalcula siempre: queda al día aunque un --rotate se corte."""
        path = self.path(name)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            self.write(name, content)

    def run(self) -> None:
        self.secrets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.secrets_dir.chmod(0o700)  # mkdir no corrige un directorio que ya existía
        for name in RANDOM:
            self.ensure(name, lambda: secrets.token_urlsafe(32))
        for caller in CALLERS:
            token = self.read(f"svc_token_{caller}")
            self.derive(f"svc_hash_{caller}", hashlib.sha256(token.encode()).hexdigest())
        token = self.read("svc_token_gateway")
        self.derive("gateway_token.conf", f'proxy_set_header X-Service-Token "{token}";\n')
        self.ensure("jwt_signing_key", new_jwt_key)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rotate", choices=ROTATABLE, help="secreto a regenerar")
    parser.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    Generator(args.dir, args.rotate).run()


if __name__ == "__main__":
    main()
