from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from shared import testing
from stego_svc.config import Settings
from stego_svc.main import create_app
from stego_svc.synthetic import embed_lsb, natural_image, png_bytes

SERVICE_DIR = Path(__file__).resolve().parents[1]
OWNER_URL, APP_URL = testing.db_urls("stego")
ANALYST = ("steganography.analyze", "steganography.results.read")
OTHER_ID = "00000000-0000-4000-8000-0000000000b2"

# Imágenes deterministas: la semilla 0 no dispara ningún detector; la misma con LSB al 50 % sí.
CLEAN = png_bytes(natural_image(0, 256))
LSB = png_bytes(embed_lsb(natural_image(0, 256), 0.5, "random"))
ZIP_AT_END = CLEAN + b"PK\x03\x04" + b"secreto" * 50


@pytest.fixture(scope="session")
def database():
    testing.prepare_database("stego", SERVICE_DIR)


@pytest.fixture
def db(database):
    testing.sql(OWNER_URL, "DELETE FROM analyses")
    return lambda statement, **params: testing.sql(OWNER_URL, statement, **params)


@pytest.fixture
def make_client(db, tmp_path):
    """Clientes que simulan al gateway; cada uno con su lifespan (pool de procesos) abierto."""
    opened = []

    def factory(url: str = APP_URL, **overrides) -> TestClient:
        values = {
            "database_url": url,
            "quarantine_dir": str(tmp_path),
            "allowed_origins": frozenset({testing.ORIGIN}),
        }
        app = create_app(
            Settings(**{**values, **overrides}),
            engine=create_async_engine(url, poolclass=NullPool),
            service_auth=testing.service_auth("stego", ("gateway",)),
        )
        client = TestClient(app, base_url=testing.ORIGIN).__enter__()
        opened.append(client)
        return client

    yield factory
    for client in opened:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    return make_client()


def analyst(user_id: str = testing.USER_ID, extra: tuple[str, ...] = ()) -> dict:
    return testing.user_headers(user_id=user_id, perms=ANALYST + extra)


def upload(client, data: bytes, name: str = "muestra.png", ctype: str = "image/png", headers=None):
    return client.post(
        "/api/steganography/analyze",
        headers=analyst() if headers is None else headers,
        files={"file": (name, data, ctype)},
    )
