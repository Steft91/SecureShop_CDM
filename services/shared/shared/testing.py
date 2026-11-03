"""Utilidades de prueba compartidas por los servicios. No se usan en producción.

Todas las contraseñas y tokens de este módulo son FIJOS y existen solo para pruebas.
"""

import asyncio
import os
from pathlib import Path

import asyncpg
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from shared.crypto import sha256
from shared.service_auth import TOKEN_HEADER, ServiceAuth

ORIGIN = "https://testserver"
ROLE_PASSWORD = "solo-pruebas"
TOKENS = {name: f"token-de-prueba-{name}" for name in ("gateway", "auth", "stego")}
USER_ID = "00000000-0000-4000-8000-0000000000a1"
SESSION_ID = "00000000-0000-4000-8000-000000000051"


def service_auth(name: str, callers: tuple[str, ...]) -> ServiceAuth:
    """ServiceAuth de prueba con los hashes de los llamadores permitidos."""
    return ServiceAuth(name, {caller: sha256(TOKENS[caller].encode()) for caller in callers})


def service_headers(name: str) -> dict:
    return {TOKEN_HEADER: TOKENS[name]}


def gateway_headers() -> dict:
    return {TOKEN_HEADER: TOKENS["gateway"], "origin": ORIGIN}


def user_headers(
    user_id: str = USER_ID,
    username: str = "ana",
    session_id: str = SESSION_ID,
    perms: tuple[str, ...] = (),
) -> dict:
    """La identidad que pone el gateway después de verificar el JWT con auth (spec §4.3)."""
    headers = {
        **gateway_headers(),
        "X-User-Id": user_id,
        "X-User-Name": username,
        "X-Session-Id": session_id,
    }
    if perms:  # Nginx no envía una cabecera vacía: sin permisos, X-User-Perms no viene
        headers["X-User-Perms"] = ",".join(perms)
    return headers


def cookie_header(cookies: dict) -> dict:
    return {"cookie": "; ".join(f"{name}={value}" for name, value in cookies.items())}


def events(caplog, action: str | None = None) -> list[dict]:
    """Eventos de shared.audit que capturó el fixture caplog, en orden."""
    return [
        {"action": r.getMessage(), "severity": r.levelname.lower(), **r.event}
        for r in caplog.records
        if r.name == "audit" and (action is None or r.getMessage() == action)
    ]


# --- PostgreSQL de pruebas (deploy/docker-compose.test.yml) ------------------------
# 127.0.0.1 y no "localhost": el compose solo publica en IPv4, y en Windows "localhost" prueba
# primero ::1 y espera ~2 s el rechazo en cada conexión.
PG_HOST = os.environ.get("TEST_PG_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("TEST_PG_PORT", "5433"))
PG_SUPERUSER_PASSWORD = os.environ.get("TEST_PG_PASSWORD", "postgres")
FOREIGN_DB = "otra_bd_test"  # BD ajena: ningún rol <svc>_app debe poder conectarse


def dsn(user: str, password: str, database: str, driver: str = "postgresql+asyncpg") -> str:
    return f"{driver}://{user}:{password}@{PG_HOST}:{PG_PORT}/{database}"


def db_urls(service: str) -> tuple[str, str]:
    """(url del rol owner, url del rol app) de la BD <service>_test."""
    database = f"{service}_test"
    return (
        dsn(f"{service}_owner", ROLE_PASSWORD, database),
        dsn(f"{service}_app", ROLE_PASSWORD, database),
    )


async def _recreate(service: str) -> None:
    conn = await asyncpg.connect(
        dsn("postgres", PG_SUPERUSER_PASSWORD, "postgres", driver="postgresql")
    )
    try:
        database = f"{service}_test"
        await conn.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        for role in (f"{service}_owner", f"{service}_app"):
            if not await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", role):
                await conn.execute(f"CREATE ROLE {role} LOGIN PASSWORD '{ROLE_PASSWORD}'")
        await conn.execute(f'CREATE DATABASE "{database}" OWNER {service}_owner')
        await conn.execute(f'REVOKE ALL ON DATABASE "{database}" FROM PUBLIC')
        await conn.execute(f'GRANT CONNECT ON DATABASE "{database}" TO {service}_app')
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", FOREIGN_DB):
            await conn.execute(f'CREATE DATABASE "{FOREIGN_DB}"')
            await conn.execute(f'REVOKE ALL ON DATABASE "{FOREIGN_DB}" FROM PUBLIC')
        # Como en producción (FND-6, init.sh): los roles de la app no entran a las BD por defecto.
        await conn.execute("REVOKE ALL ON DATABASE postgres, template1 FROM PUBLIC")
    finally:
        await conn.close()


def prepare_database(service: str, service_dir: Path) -> None:
    """Recrea <service>_test con los roles reales y aplica las migraciones como en producción.

    Alembic corre en este proceso y recibe la URL en config.attributes: la contraseña de prueba no
    pasa por el entorno, y en producción shared.migrations solo la lee del secreto.
    """
    if PG_HOST not in ("127.0.0.1", "localhost", "::1"):  # borra BD y crea roles con nombres reales
        raise RuntimeError(f"prepare_database solo contra un PostgreSQL local, no {PG_HOST}")
    asyncio.run(_recreate(service))
    config = Config(str(Path(service_dir) / "alembic.ini"))
    config.set_main_option("script_location", str(Path(service_dir) / "migrations"))
    config.attributes["url"] = db_urls(service)[0]
    command.upgrade(config, "head")


def run(coro):
    return asyncio.run(coro)


async def _with_engine(url: str, fn):
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        return await fn(engine)
    finally:
        await engine.dispose()


def sql(url: str, statement: str, **params) -> list[dict]:
    """Ejecuta SQL en una transacción propia y devuelve las filas como dicts."""

    async def go(engine):
        async with engine.begin() as conn:
            result = await conn.execute(text(statement), params)
            return [dict(row) for row in result.mappings()] if result.returns_rows else []

    return run(_with_engine(url, go))


def with_conn(url: str, fn, *args):
    """Ejecuta `await fn(conn, *args)` dentro de una transacción con el rol de la URL."""

    async def go(engine):
        async with engine.begin() as conn:
            return await fn(conn, *args)

    return run(_with_engine(url, go))


def truncate_all(owner_url: str) -> None:
    sql(
        owner_url,
        "DO $$ DECLARE t text; BEGIN "
        "FOR t IN SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' AND tablename <> 'alembic_version' LOOP "
        "EXECUTE format('TRUNCATE %I RESTART IDENTITY CASCADE', t); END LOOP; END $$",
    )


# Lo que el rol de la app NO debe tener (R11). Se pregunta al catálogo con ese mismo rol, así que
# no depende del idioma de los mensajes de Postgres. Cada fila es un privilegio de más.
_EXCESS_SQL = """
SELECT 'atributo del rol' AS falla, rolname::text AS objeto FROM pg_roles
 WHERE rolname = current_user
   AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
UNION ALL
SELECT 'miembro de otro rol', roleid::regrole::text FROM pg_auth_members
 WHERE member = current_user::regrole
UNION ALL
SELECT 'CREATE o TEMP en la BD', current_database()::text
 WHERE has_database_privilege(current_database(), 'CREATE')
    OR has_database_privilege(current_database(), 'TEMP')
UNION ALL
SELECT 'CREATE en el schema', nspname::text FROM pg_namespace
 WHERE has_schema_privilege(oid, 'CREATE')
UNION ALL
SELECT 'dueño o TRUNCATE/REFERENCES/TRIGGER', c.oid::regclass::text
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE left(n.nspname, 3) <> 'pg_' AND n.nspname <> 'information_schema'
   AND (pg_has_role(c.relowner, 'USAGE')
        OR (c.relkind IN ('r', 'p') AND (has_table_privilege(c.oid, 'TRUNCATE')
            OR has_table_privilege(c.oid, 'REFERENCES') OR has_table_privilege(c.oid, 'TRIGGER'))))
UNION ALL
SELECT 'CONNECT a otra BD', datname::text FROM pg_database
 WHERE datallowconn AND datname <> current_database()
   AND has_database_privilege(datname, 'CONNECT')
"""


def assert_least_privilege(app_url: str, table: str) -> None:
    """R11: el rol de la app lee su tabla, pero no tiene atributos ni membresías, no crea objetos,
    no es dueño de nada, no hace TRUNCATE/REFERENCES/TRIGGER y no entra a otra BD."""
    if sql(app_url, "SELECT has_table_privilege(:t, 'SELECT') AS ok", t=table) != [{"ok": True}]:
        raise AssertionError(f"el rol de la app no lee {table}: ¿es la URL correcta?")
    excess = sql(app_url, _EXCESS_SQL)
    if excess:
        raise AssertionError(f"el rol de la app tiene privilegios de más: {excess}")
