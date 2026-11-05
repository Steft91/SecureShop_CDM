"""Pruebas de perfil y cierre de sesión revocable (spec §23.4, §23.6)."""

from conftest import PASSWORD, check, create_user, identity, login

from shared import testing


def test_profile_y_logout(client, db, caplog):
    create_user(db, "ana", roles=("USER",))
    res_login = login(client, "ana", password=PASSWORD)
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]

    headers = identity(client, token)
    r = client.get("/api/auth/profile", headers=headers)
    assert r.status_code == 200
    profile_data = r.json()
    assert profile_data["username"] == "ana"
    assert profile_data["email"] == "ana@example.com"
    assert profile_data["status"] == "active"
    assert profile_data["roles"] == ["USER"]
    assert profile_data["permissions"] == []

    # Cierre de sesión -> 204
    r_out = client.post("/api/auth/logout", headers=headers)
    assert r_out.status_code == 204

    # user_sessions actualizada con ended_at y end_reason = 'logout'
    [session_row] = db(
        "SELECT ended_at, end_reason FROM user_sessions WHERE id = :sid",
        sid=headers["X-Session-Id"],
    )
    assert session_row["ended_at"] is not None
    assert session_row["end_reason"] == "logout"
    assert testing.events(caplog, "auth.logout")

    # El mismo JWT da 401 después en check
    r_check = check(client, token=token)
    assert r_check.status_code == 401
    assert r_check.json() == {"allowed": False, "reason": "session_ended"}


def test_perfil_sin_autenticacion_401(client):
    assert client.get("/api/auth/profile").status_code == 401


def test_logout_sin_autenticacion_401(client):
    assert client.post("/api/auth/logout").status_code == 401
