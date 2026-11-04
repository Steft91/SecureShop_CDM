"""Pruebas de alta del admin global por CLI y función create_admin (R4, spec §23.4)."""

import io
import sys

import pytest
from conftest import PASSWORD, check, login
from sqlalchemy.exc import IntegrityError

from auth_svc.accounts import create_admin
from auth_svc.create_admin import main
from shared import testing


def test_crea_admin_con_argon2id_y_rol_admin(app, db, caplog):
    testing.run(create_admin(app.state.engine, "  ROOT ", PASSWORD, "root@example.com"))
    [row] = db(
        "SELECT u.username, u.email, u.password_hash, r.name AS role FROM users u "
        "JOIN user_roles ur ON ur.user_id = u.id JOIN roles r ON r.id = ur.role_id "
        "WHERE u.username = 'root'"
    )
    assert (row["username"], row["email"], row["role"]) == ("root", "root@example.com", "ADMIN")
    assert row["password_hash"].startswith("$argon2id$")
    assert testing.events(caplog, "admin.create")[0]["target"] == "root"


def test_el_admin_entra_con_su_contraseña_y_tiene_todos_los_permisos(client, admin):
    res_login = login(client, admin)
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]

    r = check(client, token=token, uri="/api/users")
    assert r.status_code == 200
    assert r.headers["x-user-perms"] == (
        "roles.manage,steganography.analyze,steganography.results.read,"
        "steganography.results.read_any,users.manage"
    )


@pytest.mark.parametrize(
    ("username", "password", "email"),
    [
        ("root", "debil", "r@ex.com"),
        ("x", PASSWORD, "r@ex.com"),
        ("con espacio", PASSWORD, "r@ex.com"),
        ("rootroot1234", "RootRoot1234", "r@ex.com"),
        ("root", PASSWORD, "correo-invalido"),
    ],
)
def test_politica_de_alta(app, username, password, email):
    with pytest.raises(ValueError):
        testing.run(create_admin(app.state.engine, username, password, email))


def test_usuario_duplicado(app, admin):
    with pytest.raises(IntegrityError):
        testing.run(create_admin(app.state.engine, "ROOT", PASSWORD, "root2@example.com"))


def test_correo_duplicado(app, admin):
    with pytest.raises(IntegrityError):
        testing.run(create_admin(app.state.engine, "otro_admin", PASSWORD, "root@example.com"))


def test_cli_crea_admin_con_password_stdin(app, db, caplog, monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["create_admin", "cliadmin", "--email", "cli@example.com", "--password-stdin"],
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"{PASSWORD}\n"))
    monkeypatch.setattr("auth_svc.create_admin.load_settings", lambda: app.state.settings)

    main()
    captured = capsys.readouterr()
    assert "admin cliadmin creado" in captured.out

    [row] = db(
        "SELECT u.username, r.name AS role FROM users u "
        "JOIN user_roles ur ON ur.user_id = u.id JOIN roles r ON r.id = ur.role_id "
        "WHERE u.username = 'cliadmin'"
    )
    assert (row["username"], row["role"]) == ("cliadmin", "ADMIN")
    assert testing.events(caplog, "admin.create")[0]["target"] == "cliadmin"


def test_cli_contraseñas_no_coinciden(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["create_admin", "mismatch_admin"])
    passwords = iter(["ClaveValida123!", "OtraClaveDistinta123!"])
    monkeypatch.setattr("auth_svc.create_admin.getpass", lambda _: next(passwords))

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == "las contraseñas no coinciden"


def test_cli_usuario_duplicado_sale_con_error(app, admin, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["create_admin", "root", "--email", "otro@example.com", "--password-stdin"]
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"{PASSWORD}\n"))
    monkeypatch.setattr("auth_svc.create_admin.load_settings", lambda: app.state.settings)

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == "ese usuario o correo ya existe"
