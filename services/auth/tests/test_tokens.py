import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import jwt
from conftest import JWT_KEY
from cryptography.hazmat.primitives import serialization

from auth_svc.tokens import Signer
from shared.crypto import b64e

SIGNER = Signer(JWT_KEY, "auth", "secure-chat")


def issue(**overrides) -> str:
    values = {
        "user_id": "u1",
        "username": "ana",
        "session_id": "s1",
        "roles": ["admin"],
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
    }
    return SIGNER.issue(**{**values, **overrides})


def test_ida_y_vuelta_con_rs256():
    token = issue()
    claims = SIGNER.read(token)
    assert (claims["sub"], claims["sid"], claims["name"], claims["roles"]) == (
        "u1",
        "s1",
        "ana",
        ["admin"],
    )
    assert jwt.get_unverified_header(token)["alg"] == "RS256"


def test_vencido_alterado_o_de_otra_audiencia_es_none():
    assert SIGNER.read(issue(expires_at=datetime.now(UTC) - timedelta(seconds=1))) is None
    head, body, sig = issue().split(".")
    assert SIGNER.read(f"{head}.{body}.{sig[::-1]}") is None
    assert Signer(JWT_KEY, "auth", "otra-app").read(issue()) is None
    assert SIGNER.read("no-es-un-jwt") is None


def test_alg_none_y_hs256_con_la_clave_publica_se_rechazan():
    payload = jwt.decode(issue(), options={"verify_signature": False})
    body = b64e(json.dumps(payload).encode())
    unsigned = b64e(b'{"alg":"none","typ":"JWT"}') + "." + body
    assert SIGNER.read(unsigned + ".") is None
    public_pem = (
        serialization.load_pem_private_key(JWT_KEY.encode(), password=None)
        .public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    signing_input = b64e(b'{"alg":"HS256","typ":"JWT"}') + "." + body
    forged_sig = b64e(hmac.new(public_pem, signing_input.encode(), hashlib.sha256).digest())
    assert SIGNER.read(f"{signing_input}.{forged_sig}") is None
