"""Cuentas, catálogo de permisos, roles, sesiones e intentos fallidos (spec §7.1, §9.1)"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Catálogo fijo (spec §9.1): (código, descripción).
PERMISSIONS = [
    ("stego:analyze", "Usar la API de esteganografía"),
    ("users:manage", "Listar las cuentas"),
    ("roles:manage", "Crear y editar roles; asignar roles a usuarios"),
]
ADMIN_ROLE = "00000000-0000-4000-8000-000000000002"

UPGRADE = [
    "REVOKE ALL ON SCHEMA public FROM PUBLIC",
    "GRANT USAGE ON SCHEMA public TO auth_app",
    """CREATE TABLE users (
        id            uuid PRIMARY KEY,
        username      text UNIQUE NOT NULL CHECK (username ~ '^[a-z0-9_.-]{3,32}$'),
        alias         text NOT NULL CHECK (char_length(alias) BETWEEN 3 AND 32 AND alias !~ '[[:cntrl:]]'),
        password_hash text NOT NULL,
        created_at    timestamptz NOT NULL DEFAULT now()
    )""",
    "CREATE UNIQUE INDEX users_alias_key ON users (lower(alias))",  # nadie toma el alias de otro
    """CREATE TABLE permissions (
        code        text PRIMARY KEY,
        description text NOT NULL
    )""",
    """CREATE TABLE roles (
        id          uuid PRIMARY KEY,
        name        text UNIQUE NOT NULL CHECK (name ~ '^[a-z0-9_-]{3,32}$'),
        description text NOT NULL DEFAULT '',
        builtin     boolean NOT NULL DEFAULT false,
        created_at  timestamptz NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE role_permissions (
        role_id    uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        permission text NOT NULL REFERENCES permissions(code),
        PRIMARY KEY (role_id, permission)
    )""",
    """CREATE TABLE user_roles (
        user_id uuid NOT NULL REFERENCES users(id),
        role_id uuid NOT NULL REFERENCES roles(id),
        PRIMARY KEY (user_id, role_id)
    )""",
    """CREATE TABLE user_sessions (
        id          uuid PRIMARY KEY,
        user_id     uuid NOT NULL REFERENCES users(id),
        device_hash bytea NOT NULL,
        last_seen   timestamptz NOT NULL DEFAULT now(),
        expires_at  timestamptz NOT NULL,
        ended_at    timestamptz,
        end_reason  text
    )""",
    # Riesgo 13: una sola sesión viva por cuenta.
    "CREATE UNIQUE INDEX one_session_per_user ON user_sessions (user_id) WHERE ended_at IS NULL",
    """CREATE TABLE failed_attempts (
        id         bigserial PRIMARY KEY,
        key        text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )""",
    "CREATE INDEX failed_attempts_key_created ON failed_attempts (key, created_at)",
    # Las cuentas y las sesiones son evidencia: la app no las borra. El catálogo es de solo lectura.
    "GRANT SELECT, INSERT, UPDATE ON users, user_sessions TO auth_app",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON roles, role_permissions, user_roles TO auth_app",
    "GRANT SELECT ON permissions TO auth_app",
    "GRANT SELECT, INSERT ON failed_attempts TO auth_app",
    "GRANT USAGE ON SEQUENCE failed_attempts_id_seq TO auth_app",
]
DOWNGRADE = [
    "DROP TABLE failed_attempts",
    "DROP TABLE user_sessions",
    "DROP TABLE user_roles",
    "DROP TABLE role_permissions",
    "DROP TABLE roles",
    "DROP TABLE permissions",
    "DROP TABLE users",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)
    insert_permission = sa.text(
        "INSERT INTO permissions (code, description) VALUES (:code, :description)"
    )
    for code, description in PERMISSIONS:
        op.execute(insert_permission.bindparams(code=code, description=description))
    op.execute(
        sa.text(
            "INSERT INTO roles (id, name, description, builtin) "
            "VALUES (:admin, 'admin', 'Admin global de la plataforma', true)"
        ).bindparams(admin=ADMIN_ROLE)
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission) SELECT :role, code FROM permissions"
        ).bindparams(role=ADMIN_ROLE)
    )


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
