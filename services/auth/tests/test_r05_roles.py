"""Pruebas de roles, permisos, modelo N:M y guardias de seguridad (R5, spec §23.3, §23.4)."""

import pytest
from conftest import PASSWORD, check, create_user, identity, login, new_client

from shared import testing

CATALOG = [
    "roles.manage",
    "steganography.analyze",
    "steganography.results.read",
    "steganography.results.read_any",
    "users.manage",
]


@pytest.fixture
def root_headers(client, admin) -> dict:
    tok = login(client, admin, PASSWORD).json()["access_token"]
    return identity(client, tok)


def role_id(db, name: str) -> str:
    return db("SELECT id::text AS id FROM roles WHERE name = :n", n=name)[0]["id"]


def test_catalogo_de_permisos(client, root_headers):
    r = client.get("/api/roles/permissions", headers=root_headers)
    assert r.status_code == 200
    codes = [p["code"] for p in r.json()]
    assert sorted(codes) == sorted(CATALOG)


def test_crear_rol_con_permisos(client, root_headers, caplog):
    body = {
        "name": "AUDITOR",
        "description": "Auditor de seguridad",
        "permissions": ["steganography.results.read"],
    }
    r = client.post("/api/roles", json=body, headers=root_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "AUDITOR"
    assert data["description"] == "Auditor de seguridad"
    assert data["permissions"] == ["steganography.results.read"]
    assert data["status"] == "active"
    assert data["builtin"] is False

    events = testing.events(caplog, "role.created")
    assert len(events) >= 1
    assert events[0]["target"] == "AUDITOR"


def test_rol_permiso_desconocido_422(client, root_headers):
    body = {
        "name": "INVALIDO",
        "permissions": ["permiso.no.existente"],
    }
    r = client.post("/api/roles", json=body, headers=root_headers)
    assert r.status_code == 422
    assert "permiso desconocido" in r.json()["error"]


def test_rol_duplicado_409(client, root_headers):
    body = {"name": "REPETIDO", "permissions": []}
    assert client.post("/api/roles", json=body, headers=root_headers).status_code == 201

    r = client.post("/api/roles", json=body, headers=root_headers)
    assert r.status_code == 409
    assert "ya existe un rol con ese nombre" in r.json()["error"]


def test_rol_campos_de_mas_422(client, root_headers):
    body = {"name": "EXTRA", "permissions": [], "campo_invalido": True}
    assert client.post("/api/roles", json=body, headers=root_headers).status_code == 422


def test_listar_roles(client, root_headers):
    r = client.get("/api/roles", headers=root_headers)
    assert r.status_code == 200
    names = [role["name"] for role in r.json()]
    assert "ADMIN" in names
    assert "ANALYST" in names
    assert "USER" in names


def test_patch_rol_permisos_y_descripcion(client, root_headers, caplog):
    role = client.post(
        "/api/roles",
        json={"name": "EDITABLE", "description": "Original", "permissions": []},
        headers=root_headers,
    ).json()

    r = client.patch(
        f"/api/roles/{role['id']}",
        json={
            "description": "Modificado",
            "permissions": ["steganography.analyze"],
        },
        headers=root_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["description"] == "Modificado"
    assert data["permissions"] == ["steganography.analyze"]
    assert testing.events(caplog, "role.updated")


def test_patch_rol_admin_no_se_edita_409(client, root_headers, db):
    adm_id = role_id(db, "ADMIN")
    r = client.patch(
        f"/api/roles/{adm_id}",
        json={"permissions": []},
        headers=root_headers,
    )
    assert r.status_code == 409
    assert "el rol ADMIN no se edita" in r.json()["error"]


def test_n_m_dos_roles_y_dos_usuarios(client, root_headers, db):
    """Escenario T05: un usuario con dos roles y un rol en dos usuarios."""
    u1 = create_user(db, username="u_uno", email="u1@example.com")
    u2 = create_user(db, username="u_dos", email="u2@example.com")
    analyst_id = role_id(db, "ANALYST")
    user_id_role = role_id(db, "USER")

    # u1 recibe ANALYST y USER
    assert (
        client.post(
            "/api/user-roles",
            json={"user_id": u1, "role_id": analyst_id},
            headers=root_headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/user-roles",
            json={"user_id": u1, "role_id": user_id_role},
            headers=root_headers,
        ).status_code
        == 201
    )

    # u2 también recibe ANALYST
    assert (
        client.post(
            "/api/user-roles",
            json={"user_id": u2, "role_id": analyst_id},
            headers=root_headers,
        ).status_code
        == 201
    )

    # En GET /api/users se verifica la relación N:M
    users_resp = client.get("/api/users", headers=root_headers).json()
    u1_data = next(u for u in users_resp if u["id"] == u1)
    u2_data = next(u for u in users_resp if u["id"] == u2)

    assert sorted([r["name"] for r in u1_data["roles"]]) == ["ANALYST", "USER"]
    assert [r["name"] for r in u2_data["roles"]] == ["ANALYST"]


def test_asignacion_repetida_409(client, root_headers, db):
    """Escenario T06: repetir asignación da 409 sin fila nueva."""
    u_id = create_user(db, username="repetidor", email="rep@example.com")
    rid = role_id(db, "ANALYST")

    r1 = client.post(
        "/api/user-roles",
        json={"user_id": u_id, "role_id": rid},
        headers=root_headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/user-roles",
        json={"user_id": u_id, "role_id": rid},
        headers=root_headers,
    )
    assert r2.status_code == 409
    assert "asignación existente" in r2.json()["error"]

    # En BD solo hay una fila
    rows = db(
        "SELECT count(*) AS n FROM user_roles WHERE user_id = CAST(:u AS uuid) AND role_id = CAST(:r AS uuid)",
        u=u_id,
        r=rid,
    )
    assert rows[0]["n"] == 1


def test_asignacion_usuario_o_rol_inexistente_404(client, root_headers, db):
    fake = "00000000-0000-4000-8000-0000000000ee"
    u_id = create_user(db, username="existente", email="ex@example.com")
    rid = role_id(db, "USER")

    # Usuario inexistente
    assert (
        client.post(
            "/api/user-roles",
            json={"user_id": fake, "role_id": rid},
            headers=root_headers,
        ).status_code
        == 404
    )
    # Rol inexistente
    assert (
        client.post(
            "/api/user-roles",
            json={"user_id": u_id, "role_id": fake},
            headers=root_headers,
        ).status_code
        == 404
    )


def test_asignacion_rol_inactivo_422(client, root_headers, db):
    u_id = create_user(db, username="para_inactivo", email="inact@example.com")
    role = client.post(
        "/api/roles",
        json={"name": "INACTIVO_ROL", "permissions": []},
        headers=root_headers,
    ).json()

    # Desactivar el rol
    client.patch(f"/api/roles/{role['id']}", json={"status": "inactive"}, headers=root_headers)

    # Intentar asignar rol inactivo
    r = client.post(
        "/api/user-roles",
        json={"user_id": u_id, "role_id": role["id"]},
        headers=root_headers,
    )
    assert r.status_code == 422
    assert "el rol está inactivo" in r.json()["error"]


def test_r05_rol_asignado_vale_en_la_siguiente_peticion(app, client, root_headers, db, caplog):
    """Asignar un rol otorga inmediatamente sus permisos al JWT existente sin reingresar."""
    ana_id = create_user(db, username="ana", email="ana@example.com")
    ana_client = new_client(app)
    tok = login(ana_client, "ana", PASSWORD).json()["access_token"]

    # Inicialmente ana no tiene roles ni permisos de análisis
    chk1 = check(ana_client, tok, uri="/api/steganography/analyze")
    assert chk1.status_code == 403

    # Admin le asigna el rol ANALYST
    analyst_id = role_id(db, "ANALYST")
    assign_resp = client.post(
        "/api/user-roles",
        json={"user_id": ana_id, "role_id": analyst_id},
        headers=root_headers,
    )
    assert assign_resp.status_code == 201

    # En la siguiente petición con el MISMO JWT, ya tiene permiso para steganography.analyze
    chk2 = check(ana_client, tok, uri="/api/steganography/analyze")
    assert chk2.status_code == 200
    assert "steganography.analyze" in chk2.headers["x-user-perms"]
    assert testing.events(caplog, "user_role.assigned")


def test_r05_rol_retirado_deja_de_valer_con_el_mismo_jwt(app, client, root_headers, db, caplog):
    """Escenario T07: DELETE /api/user-roles/{id} retira el permiso en la siguiente petición con el mismo JWT."""
    ana_id = create_user(db, username="anita", email="anita@example.com", roles=("ANALYST",))
    ana_client = new_client(app)
    tok = login(ana_client, "anita", PASSWORD).json()["access_token"]

    # Anita puede analizar con su JWT
    chk1 = check(ana_client, tok, uri="/api/steganography/analyze")
    assert chk1.status_code == 200

    # Obtener el ID de la asignación
    [ur] = db(
        "SELECT id::text AS id FROM user_roles WHERE user_id = CAST(:u AS uuid)",
        u=ana_id,
    )
    # Admin retira la asignación
    del_resp = client.delete(f"/api/user-roles/{ur['id']}", headers=root_headers)
    assert del_resp.status_code == 204

    # En la siguiente petición con el MISMO JWT, queda denegada con 403
    chk2 = check(ana_client, tok, uri="/api/steganography/analyze")
    assert chk2.status_code == 403
    assert testing.events(caplog, "user_role.revoked")


def test_r05_rol_inactivo_no_da_permisos(app, client, root_headers, db):
    """Inactivar un rol retira sus permisos a todas las cuentas que lo tienen."""
    role = client.post(
        "/api/roles",
        json={"name": "INSPECTOR", "permissions": ["steganography.analyze"]},
        headers=root_headers,
    ).json()
    u_id = create_user(db, username="inspector_user", email="insp@example.com")
    client.post(
        "/api/user-roles", json={"user_id": u_id, "role_id": role["id"]}, headers=root_headers
    )

    u_client = new_client(app)
    tok = login(u_client, "inspector_user", PASSWORD).json()["access_token"]
    assert check(u_client, tok, uri="/api/steganography/analyze").status_code == 200

    # Inactivar rol
    client.patch(f"/api/roles/{role['id']}", json={"status": "inactive"}, headers=root_headers)

    # El mismo JWT ahora falla porque el rol está inactivo
    assert check(u_client, tok, uri="/api/steganography/analyze").status_code == 403


def test_r05_no_se_quita_el_ultimo_admin(client, root_headers, db, caplog):
    """No permite retirar la asignación del último administrador activo."""
    # Obtener la asignación de ADMIN de root
    root_id = root_headers["X-User-Id"]
    [ur] = db(
        "SELECT id::text AS id FROM user_roles WHERE user_id = CAST(:u AS uuid)",
        u=root_id,
    )
    r = client.delete(f"/api/user-roles/{ur['id']}", headers=root_headers)
    assert r.status_code == 409
    assert "no se puede retirar el último administrador" in r.json()["error"]
    assert testing.events(caplog, "admin.guard.last_admin")

    # Si hay dos admins, uno sí puede ser retirado
    admin2_id = create_user(
        db, username="segundo_admin", email="adm2@example.com", roles=("ADMIN",)
    )
    [ur2] = db(
        "SELECT id::text AS id FROM user_roles WHERE user_id = CAST(:u AS uuid)",
        u=admin2_id,
    )
    assert client.delete(f"/api/user-roles/{ur2['id']}", headers=root_headers).status_code == 204


def test_r05_sin_admin_no_concede_permisos_de_admin(app, client, root_headers, db, caplog):
    """Regla anti-escalada (R5): sin rol ADMIN no se asigna/retira ADMIN ni se crean roles de admin."""
    # Crear un rol con roles.manage pero SIN ser ADMIN
    db(
        "INSERT INTO roles (id, name, description) VALUES "
        "('00000000-0000-4000-8000-0000000000bb', 'ROLE_OPERATOR', 'Operador de roles')"
    )
    db(
        "INSERT INTO role_permissions (role_id, permission) VALUES "
        "('00000000-0000-4000-8000-0000000000bb', 'roles.manage')"
    )
    create_user(db, username="operador_roles", email="op_r@example.com", roles=("ROLE_OPERATOR",))

    op_client = new_client(app)
    tok = login(op_client, "operador_roles", PASSWORD).json()["access_token"]
    op_headers = identity(client, tok)

    target_user = create_user(db, username="victima", email="vic@example.com")
    admin_rid = role_id(db, "ADMIN")

    # 1. No puede asignar el rol ADMIN
    r_assign = client.post(
        "/api/user-roles",
        json={"user_id": target_user, "role_id": admin_rid},
        headers=op_headers,
    )
    assert r_assign.status_code == 403
    assert testing.events(caplog, "authz.denied")

    # 2. No puede crear un rol con roles.manage o users.manage
    r_create = client.post(
        "/api/roles",
        json={"name": "ESCALADO", "permissions": ["roles.manage"]},
        headers=op_headers,
    )
    assert r_create.status_code == 403

    # 3. No puede editar un rol para agregar permisos administrativos
    non_adm_role = client.post(
        "/api/roles",
        json={"name": "BASICO", "permissions": ["steganography.analyze"]},
        headers=root_headers,
    ).json()

    r_patch = client.patch(
        f"/api/roles/{non_adm_role['id']}",
        json={"permissions": ["users.manage"]},
        headers=op_headers,
    )
    assert r_patch.status_code == 403


def test_sin_roles_manage_403(app, client, db, caplog):
    create_user(db, username="usuario_normal", email="norm@example.com", roles=("USER",))
    u_client = new_client(app)
    tok = login(u_client, "usuario_normal", PASSWORD).json()["access_token"]
    u_headers = identity(client, tok)

    assert client.get("/api/roles", headers=u_headers).status_code == 403
    assert (
        client.post(
            "/api/roles",
            json={"name": "NUEVO", "permissions": []},
            headers=u_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/user-roles",
            json={
                "user_id": "00000000-0000-4000-8000-000000000001",
                "role_id": "00000000-0000-4000-8000-000000000001",
            },
            headers=u_headers,
        ).status_code
        == 403
    )
    assert testing.events(caplog, "perm.denied")
