from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from auth_svc.config import Settings
from auth_svc.main import create_app
from shared import testing

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
# Limpieza entre tests SIN tocar el catálogo de permisos ni el rol semilla admin.
RESET = [
    "TRUNCATE users, failed_attempts CASCADE",  # también vacía user_roles y user_sessions
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
    """Un navegador (o un Postman) propio: su almacén de cookies es otro dispositivo."""
    return TestClient(app, base_url=testing.ORIGIN, headers=testing.gateway_headers())


@pytest.fixture
def client(app):
    return new_client(app)
