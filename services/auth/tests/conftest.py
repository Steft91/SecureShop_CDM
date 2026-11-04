from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from auth_svc.config import Settings
from auth_svc.main import create_app
from shared import testing
from shared.passwords import hash_secret

SERVICE_DIR = Path(__file__).resolve().parents[1]
OWNER_URL, APP_URL = testing.db_urls("auth")
PASSWORD = "Clave-Segura-2026"  # contraseña de prueba
# Clave de JWT solo para pruebas: 2048 bits por velocidad (producción usa 3072, FND-6).
JWT_KEY = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    .decode()
)
# Limpieza entre tests SIN tocar el catálogo de permisos ni los roles semilla.
RESET = [
    "DELETE FROM user_sessions",
    "DELETE FROM user_roles",
    "DELETE FROM users",
    "DELETE FROM failed_attempts",
    "DELETE FROM roles WHERE NOT builtin",
]


@pytest.fixture(scope="session")
def database():
    testing.prepare_database("auth", SERVICE_DIR)


@pytest.fixture
def db(database):
    for statement in RESET:
        testing.sql(OWNER_URL, statement)
    return lambda statement, **params: testing.sql(OWNER_URL, statement, **params)


def make_settings(**overrides) -> Settings:
    values = {
        "database_url": APP_URL,
        "jwt_private_key": JWT_KEY,
        "allowed_origins": frozenset({testing.ORIGIN}),
        "login_delay_base": 0,
    }
    return Settings(**{**values, **overrides})


def make_app(settings: Settings):
    return create_app(
        settings,
        engine=create_async_engine(APP_URL, poolclass=NullPool),
        service_auth=testing.service_auth("auth", ("gateway",)),
    )


@pytest.fixture
def app(db):
    return make_app(make_settings())


def new_client(app) -> TestClient:
    """Un cliente simulando peticiones que provienen del gateway."""
    return TestClient(app, base_url=testing.ORIGIN, headers=testing.gateway_headers())


@pytest.fixture
def client(app):
    return new_client(app)


def grant(db, username: str, role: str) -> None:
    db(
        "INSERT INTO user_roles (id, user_id, role_id) "
        "SELECT CAST(:id AS uuid), u.id, r.id FROM users u, roles r "
        "WHERE u.username = :u AND r.name = :r",
        id=str(uuid4()),
        u=username.strip().lower(),
        r=role,
    )


def create_user(
    db,
    username: str = "ana",
    email: str | None = None,
    password: str = PASSWORD,
    status: str = "active",
    roles: tuple[str, ...] = (),
) -> str:
    user_id = str(uuid4())
    norm_u = username.strip().lower()
    norm_email = (email or f"{norm_u}@example.com").strip().lower()
    p_hash = hash_secret(password)
    db(
        "INSERT INTO users (id, username, email, password_hash, status) "
        "VALUES (CAST(:id AS uuid), :u, :e, :h, :s)",
        id=user_id,
        u=norm_u,
        e=norm_email,
        h=p_hash,
        s=status,
    )
    for r in roles:
        grant(db, norm_u, r)
    return user_id


def login(client, username: str = "ana", password: str = PASSWORD):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def check(client, token: str | None = None, uri: str = "/api/auth/profile", **kwargs):
    """Llamada del gateway a POST /internal/authorization/check."""
    headers = {"X-Original-URI": uri}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/internal/authorization/check", headers=headers, **kwargs)


def identity(client, token: str, uri: str = "/api/auth/profile") -> dict:
    """Cabeceras que el gateway inyecta al upstream tras un check exitoso."""
    r = check(client, token=token, uri=uri)
    assert r.status_code == 200, r.text
    headers = {
        **testing.gateway_headers(),
        "X-User-Id": r.headers["x-user-id"],
        "X-User-Name": r.headers["x-user-name"],
        "X-Session-Id": r.headers["x-session-id"],
    }
    if "x-user-perms" in r.headers:
        headers["X-User-Perms"] = r.headers["x-user-perms"]
    return headers


@pytest.fixture
def admin(app) -> str:
    """El admin global 'root' (contraseña PASSWORD), creado como lo haría el CLI."""
    from auth_svc.accounts import create_admin

    testing.run(create_admin(app.state.engine, "root", PASSWORD, "root@example.com"))
    return "root"
