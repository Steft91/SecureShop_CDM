import hashlib
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SCRIPT = Path(__file__).resolve().parents[3] / "deploy" / "gen_secrets.py"


def gen(root: Path, *args: str) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--dir", str(root), *args], check=True, capture_output=True
    )


def test_genera_todo_y_no_sobrescribe(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    assert sorted(p.name for p in secrets.iterdir()) == [
        "db_auth_app",
        "db_auth_owner",
        "gateway_token.conf",
        "jwt_signing_key",
        "postgres_password",
        "svc_hash_gateway",
        "svc_token_gateway",
    ]
    jwt_key = serialization.load_pem_private_key(
        (secrets / "jwt_signing_key").read_bytes(), password=None
    )
    assert isinstance(jwt_key, rsa.RSAPrivateKey) and jwt_key.key_size == 3072
    token = (secrets / "svc_token_gateway").read_text().strip()
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(token.encode()).hexdigest()
    assert token in (secrets / "gateway_token.conf").read_text()
    before = {p.name: p.read_text() for p in secrets.iterdir()}
    gen(tmp_path)
    assert {p.name: p.read_text() for p in secrets.iterdir()} == before


def test_lo_derivado_del_token_se_repara_si_quedo_viejo(tmp_path):
    gen(tmp_path)  # p. ej. un --rotate que se cortó entre el token y su hash
    secrets = tmp_path / "secrets"
    (secrets / "svc_hash_gateway").write_text("hash-viejo")
    (secrets / "gateway_token.conf").write_text("conf-viejo")
    gen(tmp_path)
    token = (secrets / "svc_token_gateway").read_text().strip()
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(token.encode()).hexdigest()
    assert token in (secrets / "gateway_token.conf").read_text()


def test_no_rota_contrasenas_de_bd(tmp_path):
    # Postgres solo las lee al crear el volumen: rotarlas aquí rompería la conexión.
    args = [sys.executable, str(SCRIPT), "--dir", str(tmp_path), "--rotate", "db_auth_app"]
    assert subprocess.run(args, capture_output=True).returncode != 0


def test_rotar_token_del_gateway_regenera_hash_y_conf(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    old = (secrets / "svc_token_gateway").read_text().strip()
    gen(tmp_path, "--rotate", "svc_token_gateway")
    new = (secrets / "svc_token_gateway").read_text().strip()
    assert new != old
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(new.encode()).hexdigest()
    assert new in (secrets / "gateway_token.conf").read_text()
