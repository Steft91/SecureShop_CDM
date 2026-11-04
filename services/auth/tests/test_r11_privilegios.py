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
        "DELETE FROM user_sessions",
        "INSERT INTO permissions (code, description) VALUES ('x:y', 'x')",
    ],
)
def test_r11_la_app_no_borra_cuentas_ni_edita_el_catalogo(database, statement):
    with pytest.raises(Exception, match="permission denied"):
        testing.sql(APP_URL, statement)


def test_catalogo_y_rol_semilla(db):
    assert [row["code"] for row in db("SELECT code FROM permissions ORDER BY code")] == [
        "roles:manage",
        "stego:analyze",
        "users:manage",
    ]
    roles = db(
        "SELECT r.name, r.builtin, count(rp.permission) AS n FROM roles r "
        "LEFT JOIN role_permissions rp ON rp.role_id = r.id GROUP BY r.name, r.builtin"
    )
    assert roles == [{"name": "admin", "builtin": True, "n": 3}]
