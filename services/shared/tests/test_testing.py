import pytest

from shared import testing

SERVICE = "shared"  # BD shared_test con los roles shared_owner y shared_app

MIGRATION = """
from alembic import op

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE TABLE notas (id serial PRIMARY KEY, texto text NOT NULL)")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON notas TO shared_app")
    op.execute("GRANT USAGE ON SEQUENCE notas_id_seq TO shared_app")
"""


@pytest.fixture(scope="module")
def service_dir(tmp_path_factory):
    """Un servicio mínimo con Alembic, armado como services/auth (ATH-1)."""
    root = tmp_path_factory.mktemp("svc")
    (root / "alembic.ini").write_text("[alembic]\nscript_location = migrations\n", encoding="utf-8")
    versions = root / "migrations" / "versions"
    versions.mkdir(parents=True)
    env_py = f'from shared.migrations import run\n\nrun("{SERVICE}")\n'
    (root / "migrations" / "env.py").write_text(env_py, encoding="utf-8")
    (versions / "0001_notas.py").write_text(MIGRATION, encoding="utf-8")
    testing.prepare_database(SERVICE, root)
    return root


def test_sql_contra_el_postgres_de_pruebas():
    url = testing.dsn("postgres", testing.PG_SUPERUSER_PASSWORD, "postgres")
    assert testing.sql(url, "SELECT 1 AS uno") == [{"uno": 1}]


def test_prepare_database_migra_con_el_rol_owner(service_dir):
    owner_url, app_url = testing.db_urls(SERVICE)
    assert testing.sql(owner_url, "SELECT version_num FROM alembic_version") == [
        {"version_num": "0001"}
    ]
    testing.sql(app_url, "INSERT INTO notas (texto) VALUES (:texto)", texto="hola")
    assert {"texto": "hola"} in testing.sql(app_url, "SELECT texto FROM notas")


def test_truncate_all_vacia_todo_menos_alembic_version(service_dir):
    owner_url, app_url = testing.db_urls(SERVICE)
    testing.sql(app_url, "INSERT INTO notas (texto) VALUES ('x')")
    testing.truncate_all(owner_url)
    assert testing.sql(app_url, "SELECT count(*) AS n FROM notas") == [{"n": 0}]
    assert testing.sql(owner_url, "SELECT count(*) AS n FROM alembic_version") == [{"n": 1}]


def test_r11_el_rol_app_no_tiene_privilegios_de_mas(service_dir):
    _, app_url = testing.db_urls(SERVICE)
    testing.assert_least_privilege(app_url, "notas")


def test_assert_least_privilege_detecta_un_rol_con_privilegios(service_dir):
    owner_url, _ = testing.db_urls(SERVICE)
    with pytest.raises(AssertionError):
        testing.assert_least_privilege(owner_url, "notas")


SUPERUSER_URL = testing.dsn("postgres", testing.PG_SUPERUSER_PASSWORD, "postgres")


@pytest.mark.parametrize(
    ("dar", "quitar", "como"),
    [
        ("ALTER ROLE shared_app CREATEDB", "ALTER ROLE shared_app NOCREATEDB", "super"),
        (
            "GRANT TRUNCATE ON notas TO shared_app",
            "REVOKE TRUNCATE ON notas FROM shared_app",
            "owner",
        ),
        (
            f"GRANT CONNECT ON DATABASE {testing.FOREIGN_DB} TO shared_app",
            f"REVOKE CONNECT ON DATABASE {testing.FOREIGN_DB} FROM shared_app",
            "super",
        ),
    ],
)
def test_r11_un_privilegio_de_mas_no_pasa(service_dir, dar, quitar, como):
    owner_url, app_url = testing.db_urls(SERVICE)
    url = SUPERUSER_URL if como == "super" else owner_url
    testing.sql(url, dar)
    try:
        with pytest.raises(AssertionError):
            testing.assert_least_privilege(app_url, "notas")
    finally:
        testing.sql(url, quitar)


def test_prepare_database_solo_contra_un_postgres_local(monkeypatch, tmp_path):
    monkeypatch.setattr(testing, "PG_HOST", "db.example.com")
    with pytest.raises(RuntimeError, match="solo contra un PostgreSQL local"):
        testing.prepare_database(SERVICE, tmp_path)
