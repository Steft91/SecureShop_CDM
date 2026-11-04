import pytest
from conftest import APP_URL

from shared import testing


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_r11_rol_app_confinado(database):
    testing.assert_least_privilege(APP_URL, table="users")


@pytest.mark.parametrize(
    "statement",
    [
        "DELETE FROM users",
        "DELETE FROM roles",
        "INSERT INTO permissions (code, description) VALUES ('x.y', 'x')",
    ],
)
def test_r11_la_app_no_borra_cuentas_ni_edita_el_catalogo(database, statement):
    with pytest.raises(Exception, match="permission denied|permiso denegado"):
        testing.sql(APP_URL, statement)


def test_catalogo_y_roles_semilla(db):
    assert [row["code"] for row in db("SELECT code FROM permissions ORDER BY code")] == [
        "roles.manage",
        "steganography.analyze",
        "steganography.results.read",
        "steganography.results.read_any",
        "users.manage",
    ]
    roles = {
        row["name"]: (row["builtin"], row["n"])
        for row in db(
            "SELECT r.name, r.builtin, count(rp.permission) AS n FROM roles r "
            "LEFT JOIN role_permissions rp ON rp.role_id = r.id GROUP BY r.name, r.builtin"
        )
    }
    assert roles["ADMIN"] == (True, 5)
    assert roles["ANALYST"] == (True, 2)
    assert roles["USER"] == (True, 0)


def test_modelo_n_m_con_fk_y_unicidad(db):
    u1 = "00000000-0000-4000-8000-000000000010"
    u2 = "00000000-0000-4000-8000-000000000011"
    admin_role = "00000000-0000-4000-8000-000000000001"
    db(
        "INSERT INTO users (id, username, email, password_hash) VALUES (CAST(:id AS uuid), :u, :e, :p)",
        id=u1,
        u="user1",
        e="user1@example.com",
        p="hash1",
    )
    with pytest.raises(
        Exception, match="duplicate key|unique constraint|llave duplicada|violaci|restricci"
    ):
        db(
            "INSERT INTO users (id, username, email, password_hash) VALUES (CAST(:id AS uuid), :u, :e, :p)",
            id=u2,
            u="user1",
            e="user2@example.com",
            p="hash2",
        )
    with pytest.raises(
        Exception, match="duplicate key|unique constraint|llave duplicada|violaci|restricci"
    ):
        db(
            "INSERT INTO users (id, username, email, password_hash) VALUES (CAST(:id AS uuid), :u, :e, :p)",
            id=u2,
            u="user2",
            e="user1@example.com",
            p="hash2",
        )
    ur1 = "00000000-0000-4000-8000-000000000020"
    ur2 = "00000000-0000-4000-8000-000000000021"
    db(
        "INSERT INTO user_roles (id, user_id, role_id) VALUES (CAST(:id AS uuid), CAST(:u AS uuid), CAST(:r AS uuid))",
        id=ur1,
        u=u1,
        r=admin_role,
    )
    with pytest.raises(
        Exception, match="duplicate key|unique constraint|llave duplicada|violaci|restricci"
    ):
        db(
            "INSERT INTO user_roles (id, user_id, role_id) VALUES (CAST(:id AS uuid), CAST(:u AS uuid), CAST(:r AS uuid))",
            id=ur2,
            u=u1,
            r=admin_role,
        )
