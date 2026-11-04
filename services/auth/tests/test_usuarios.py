"""Pruebas de administración de usuarios (R4, R5, spec §23.4)."""

import pytest
from conftest import PASSWORD, check, create_user, identity, login, new_client

from shared import testing


@pytest.fixture
def root_headers(client, admin) -> dict:
    token = login(client, admin, PASSWORD).json()["access_token"]
    return identity(client, token)


def test_admin_crea_cuenta_sin_roles(app, client, root_headers, caplog, db):
    """La cuenta nace sin roles, con hash Argon2id y evento user.created."""
    body = {
        "username": "operador1",
        "email": "operador1@example.com",
        "password": "Password-Seguro-2026",
    }
    r = client.post("/api/users", json=body, headers=root_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "operador1"
    assert data["email"] == "operador1@example.com"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data

    # En BD el hash es Argon2id
    [row] = db(
        "SELECT password_hash, status FROM users WHERE id = CAST(:id AS uuid)",
        id=data["id"],
    )
    assert row["password_hash"].startswith("$argon2id$")
    assert row["status"] == "active"

    # En el listado no tiene roles
    users_resp = client.get("/api/users", headers=root_headers)
    user_in_list = next(u for u in users_resp.json() if u["username"] == "operador1")
    assert user_in_list["roles"] == []

    # Login y check: sesión autenticada pero sin permisos para rutas protegidas
    op_client = new_client(app)
    tok = login(op_client, "operador1", "Password-Seguro-2026").json()["access_token"]
    chk_session = check(op_client, tok, uri="/api/auth/profile")
    assert chk_session.status_code == 200
    assert "x-user-perms" not in chk_session.headers

    chk_protected = check(op_client, tok, uri="/api/users")
    assert chk_protected.status_code == 403

    # Evento de auditoría emitido
    events = testing.events(caplog, "user.created")
    assert len(events) >= 1
    assert events[0]["target"] == "operador1"


def test_usuario_o_correo_duplicado_409(client, root_headers):
    """No permite usuarios ni correos duplicados."""
    body = {
        "username": "duplicado",
        "email": "dup@example.com",
        "password": "Password-Seguro-2026",
    }
    assert client.post("/api/users", json=body, headers=root_headers).status_code == 201

    # Repetir username
    r1 = client.post(
        "/api/users",
        json={
            "username": "DUPLICADO",
            "email": "otro@example.com",
            "password": "Password-Seguro-2026",
        },
        headers=root_headers,
    )
    assert r1.status_code == 409
    assert "usuario no disponible" in r1.json()["error"]

    # Repetir email
    r2 = client.post(
        "/api/users",
        json={
            "username": "otro_user",
            "email": "dup@example.com",
            "password": "Password-Seguro-2026",
        },
        headers=root_headers,
    )
    assert r2.status_code == 409
    assert "usuario no disponible" in r2.json()["error"]


@pytest.mark.parametrize(
    ("username", "email", "password"),
    [
        ("ab", "valido@example.com", "Password-Seguro-2026"),  # username corto
        ("con espacios", "valido@example.com", "Password-Seguro-2026"),  # espacios
        ("valido", "sin-arroba", "Password-Seguro-2026"),  # email inválido
        ("valido", "valido@example.com", "corta"),  # contraseña corta
        ("valido", "valido@example.com", "solominusculas123"),  # sin mayúsculas ni símbolos
        ("clave-igual-usuario", "valido@example.com", "Clave-Igual-Usuario"),  # igual al usuario
    ],
)
def test_crear_usuario_credenciales_invalidas_422(client, root_headers, username, email, password):
    r = client.post(
        "/api/users",
        json={"username": username, "email": email, "password": password},
        headers=root_headers,
    )
    assert r.status_code == 422


def test_crear_usuario_campos_de_mas_422(client, root_headers):
    body = {
        "username": "valido",
        "email": "valido@example.com",
        "password": "Password-Seguro-2026",
        "extra_field": "inyeccion",
    }
    assert client.post("/api/users", json=body, headers=root_headers).status_code == 422


def test_listar_usuarios(app, client, root_headers, db):
    u1 = create_user(db, username="user1", email="user1@example.com", roles=("ANALYST", "USER"))
    u2 = create_user(db, username="user2", email="user2@example.com", roles=())

    r = client.get("/api/users", headers=root_headers)
    assert r.status_code == 200
    users = r.json()
    assert len(users) >= 3  # root + user1 + user2

    u1_entry = next(u for u in users if u["id"] == u1)
    assert u1_entry["username"] == "user1"
    role_names = [role["name"] for role in u1_entry["roles"]]
    assert sorted(role_names) == ["ANALYST", "USER"]
    for role in u1_entry["roles"]:
        assert "assignment_id" in role
        assert "role_id" in role

    u2_entry = next(u for u in users if u["id"] == u2)
    assert u2_entry["roles"] == []


def test_patch_usuario_actualiza_correo(client, root_headers, db, caplog):
    u_id = create_user(db, username="modificable", email="viejo@example.com")
    r = client.patch(
        f"/api/users/{u_id}",
        json={"email": "nuevo@example.com"},
        headers=root_headers,
    )
    assert r.status_code == 200
    assert r.json()["email"] == "nuevo@example.com"
    [row] = db("SELECT email FROM users WHERE id = CAST(:id AS uuid)", id=u_id)
    assert row["email"] == "nuevo@example.com"
    assert testing.events(caplog, "user.updated")


def test_patch_usuario_correo_duplicado_409(client, root_headers, db):
    create_user(db, username="primero", email="primero@example.com")
    u2 = create_user(db, username="segundo", email="segundo@example.com")
    r = client.patch(
        f"/api/users/{u2}",
        json={"email": "primero@example.com"},
        headers=root_headers,
    )
    assert r.status_code == 409


def test_patch_usuario_inactivar_termina_sesiones(app, client, root_headers, db):
    """Inactivar un usuario termina sus sesiones activas inmediatamente."""
    u_id = create_user(db, username="sesionero", email="sesionero@example.com")
    user_client = new_client(app)
    tok = login(user_client, "sesionero", PASSWORD).json()["access_token"]
    assert check(user_client, tok).status_code == 200

    # Inactivar cuenta
    r = client.patch(f"/api/users/{u_id}", json={"status": "inactive"}, headers=root_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "inactive"

    # En BD la sesión quedó finalizada
    [sess] = db(
        "SELECT ended_at, end_reason FROM user_sessions WHERE user_id = CAST(:id AS uuid)", id=u_id
    )
    assert sess["ended_at"] is not None
    assert sess["end_reason"] == "user_inactive"

    # El token previo ahora es rechazado con 401
    chk = check(user_client, tok)
    assert chk.status_code == 401


def test_patch_usuario_nadie_se_desactiva_a_si_mismo(client, root_headers):
    me = root_headers["X-User-Id"]
    r = client.patch(f"/api/users/{me}", json={"status": "inactive"}, headers=root_headers)
    assert r.status_code == 409
    assert "no puedes desactivar tu propia cuenta" in r.json()["error"]


def test_patch_usuario_no_desactiva_al_ultimo_admin(app, client, root_headers, db, caplog):
    """Con dos admins se puede desactivar a uno, pero no al último."""
    # Crear un segundo admin
    admin2_id = create_user(db, username="admin2", email="admin2@example.com", roles=("ADMIN",))

    # root desactiva a admin2: debe permitirse porque queda root
    r = client.patch(f"/api/users/{admin2_id}", json={"status": "inactive"}, headers=root_headers)
    assert r.status_code == 200

    # Crear un usuario con rol especial que tiene permiso users.manage
    db(
        "INSERT INTO roles (id, name, description) VALUES "
        "('00000000-0000-4000-8000-0000000000aa', 'USER_MANAGER', 'Gestor de cuentas')"
    )
    db(
        "INSERT INTO role_permissions (role_id, permission) VALUES "
        "('00000000-0000-4000-8000-0000000000aa', 'users.manage')"
    )
    create_user(db, username="gestor", email="gestor@example.com", roles=("USER_MANAGER",))
    mgr_tok = login(new_client(app), "gestor", PASSWORD).json()["access_token"]
    mgr_headers = identity(client, mgr_tok)

    # El gestor (que no es root) intenta desactivar a root (que es el ÚLTIMO admin activo):
    root_id = root_headers["X-User-Id"]
    r_last = client.patch(f"/api/users/{root_id}", json={"status": "inactive"}, headers=mgr_headers)
    assert r_last.status_code == 409
    assert "no se puede desactivar al último administrador" in r_last.json()["error"]
    assert testing.events(caplog, "admin.guard.last_admin")


def test_patch_usuario_inexistente_404(client, root_headers):
    fake_id = "00000000-0000-4000-8000-0000000000ee"
    assert (
        client.patch(
            f"/api/users/{fake_id}", json={"status": "inactive"}, headers=root_headers
        ).status_code
        == 404
    )


def test_usuarios_sin_permiso_users_manage_403(app, client, db, caplog):
    u_id = create_user(db, username="regular", email="reg@example.com", roles=("USER",))
    user_client = new_client(app)
    tok = login(user_client, "regular", PASSWORD).json()["access_token"]
    user_headers = identity(client, tok)

    assert client.get("/api/users", headers=user_headers).status_code == 403
    assert (
        client.post(
            "/api/users",
            json={"username": "x", "email": "x@x.com", "password": PASSWORD},
            headers=user_headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/users/{u_id}", json={"status": "inactive"}, headers=user_headers
        ).status_code
        == 403
    )
    assert testing.events(caplog, "perm.denied")
