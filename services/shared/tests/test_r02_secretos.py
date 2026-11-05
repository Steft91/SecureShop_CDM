import pytest

from shared.secrets import db_url, env, origins, read_secret


@pytest.fixture
def secrets_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    return tmp_path


def write(directory, name, value):
    (directory / name).write_text(value, encoding="utf-8")


def test_secreto_ausente_detiene_el_servicio(secrets_dir):
    with pytest.raises(RuntimeError, match="secreto requerido ausente: jwt_signing_key"):
        read_secret("jwt_signing_key")


def test_secreto_vacio_tambien_lo_detiene(secrets_dir):
    write(secrets_dir, "jwt_signing_key", "  \n")
    with pytest.raises(RuntimeError, match="secreto vacío: jwt_signing_key"):
        read_secret("jwt_signing_key")


def test_lee_secreto_y_url_de_bd(secrets_dir, monkeypatch):
    write(secrets_dir, "svc_hash_gateway", "abc123\n")
    write(secrets_dir, "db_auth_app", "p@ss/word")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    assert read_secret("svc_hash_gateway") == "abc123"
    assert (
        db_url("auth", "app") == "postgresql+asyncpg://auth_app:p%40ss%2Fword@localhost:5433/auth"
    )


def test_env_convierte_tipos(monkeypatch):
    monkeypatch.setenv("UN_ENTERO", "3")
    monkeypatch.setenv("UN_REAL", "0.5")
    monkeypatch.setenv("STEGO_ENTROPY_TRIGGER", "off")
    assert env("UN_ENTERO", 10) == 3
    assert env("UN_REAL", 5.0) == 0.5
    assert env("STEGO_ENTROPY_TRIGGER", None) is None
    assert env("NO_EXISTE", 7) == 7


def test_origins_separa_por_comas(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a, https://b,")
    assert origins() == frozenset({"https://a", "https://b"})
