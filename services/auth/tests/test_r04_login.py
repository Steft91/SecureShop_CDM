"""Pruebas de login, rate limiting y eventos (R4, R5, spec §23.4)."""

import jwt
from conftest import PASSWORD, create_user, login
from fastapi.testclient import TestClient

from shared import testing


def test_login_entrega_jwt_y_sesion(client, db, caplog):
    create_user(db, "ana")
    r = login(client, "ana")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "Bearer"
    assert 0 < body["expires_in"] <= 15 * 60
    assert len(client.cookies) == 0  # Sin cookies en el primer parcial
    claims = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert (claims["name"], claims["roles"]) == ("ana", [])
    assert db("SELECT count(*) AS n FROM user_sessions WHERE ended_at IS NULL") == [{"n": 1}]
    ev = testing.events(caplog, "auth.login.ok")[0]
    assert ev["actor"] == "user:ana"
    assert "access_token" not in str(ev)
    assert PASSWORD not in str(ev)


def test_error_generico_para_clave_mala_y_usuario_inexistente(client, db, caplog):
    create_user(db, "ana")
    malo = login(client, "ana", password="incorrecta")
    nadie = login(client, username="nadie", password="incorrecta")
    assert malo.status_code == nadie.status_code == 401
    assert malo.json() == nadie.json() == {"error": "credenciales inválidas"}
    assert len(testing.events(caplog, "auth.login.fail")) == 2


def test_usuario_normalizado_al_crear_y_en_login(client, db):
    create_user(db, "ana")
    assert login(client, username="  ANA ").status_code == 200
    assert login(client, username=" Ana").status_code == 200


def test_r04_bloqueo_tras_5_fallos_por_usuario(client, db, caplog):
    create_user(db, "ana")
    for _ in range(5):
        assert login(client, "ana", password="incorrecta").status_code == 401
    r = login(client, "ana")
    assert r.status_code == 429
    assert r.headers["retry-after"] == "900"
    assert testing.events(caplog, "auth.login.locked")


def test_r04_bloqueo_por_ip_aunque_cambie_el_usuario(app, db):
    create_user(db, "ana")
    attacker = TestClient(
        app, base_url=testing.ORIGIN, headers=testing.gateway_headers(), client=("10.9.9.9", 4000)
    )
    for i in range(5):
        login(attacker, username=f"user{i}", password="x")
    assert login(attacker, username="ana").status_code == 429


def test_cuenta_inactiva_403_despues_de_verificar_contraseña(client, db, caplog):
    create_user(db, "inactiva", status="inactive")
    # Clave incorrecta -> 401 (no delata que la cuenta está inactiva)
    assert login(client, "inactiva", password="incorrecta").status_code == 401
    # Clave correcta pero cuenta inactiva -> 403
    r = login(client, "inactiva", password=PASSWORD)
    assert r.status_code == 403
    assert r.json() == {"error": "cuenta inactiva"}
    assert testing.events(caplog, "auth.login.inactive")


def test_cuerpo_con_campos_extra_422(client):
    r = client.post(
        "/api/auth/login",
        json={"username": "ana", "password": PASSWORD, "extra": "campo_no_permitido"},
    )
    assert r.status_code == 422
