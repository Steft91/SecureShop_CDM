"""Pruebas de decisión de autorización interna (R5, R16, spec §23.6)."""

from datetime import UTC, datetime, timedelta

import jwt
from conftest import check, create_user, grant, login

from shared import testing
from shared.crypto import b64e


def test_check_decide_por_accion(client, db, caplog):
    # 1. Usuario sin roles: solo accede a session (profile y logout)
    create_user(db, "ana")
    token_ana = login(client, "ana").json()["access_token"]

    r_prof = check(client, token=token_ana, uri="/api/auth/profile")
    assert r_prof.status_code == 200
    assert r_prof.json()["allowed"] is True
    assert r_prof.json()["action"] == "session"
    assert r_prof.headers["x-user-name"] == "ana"
    assert "x-user-perms" not in r_prof.headers

    r_logout = check(client, token=token_ana, uri="/api/auth/logout")
    assert r_logout.status_code == 200
    assert r_logout.json()["allowed"] is True

    r_users = check(client, token=token_ana, uri="/api/users")
    assert r_users.status_code == 403
    assert r_users.json()["allowed"] is False
    assert r_users.json()["reason"] == "no_active_role_grants_permission"
    assert testing.events(caplog, "authz.denied")

    # 2. Analista: steganography.analyze y steganography.results.read
    create_user(db, "carlos", roles=("ANALYST",))
    token_carlos = login(client, "carlos").json()["access_token"]

    r_analyze = check(client, token=token_carlos, uri="/api/steganography/analyze")
    assert r_analyze.status_code == 200
    assert r_analyze.json()["allowed"] is True
    assert r_analyze.json()["action"] == "steganography.analyze"

    r_results = check(client, token=token_carlos, uri="/api/steganography/results/uuid-123")
    assert r_results.status_code == 200
    assert r_results.json()["allowed"] is True
    assert r_results.json()["action"] == "steganography.results.read"

    r_carlos_users = check(client, token=token_carlos, uri="/api/users")
    assert r_carlos_users.status_code == 403

    # 3. Admin: users.manage, roles.manage y stego
    grant(db, "ana", "ADMIN")
    r_admin_users = check(client, token=token_ana, uri="/api/users")
    assert r_admin_users.status_code == 200
    assert r_admin_users.json()["allowed"] is True
    assert "users.manage" in r_admin_users.headers["x-user-perms"]


def test_check_comparacion_segmentos_completos(client, db):
    create_user(db, "admin", roles=("ADMIN",))
    token = login(client, "admin").json()["access_token"]

    # Coincidencias válidas
    assert check(client, token=token, uri="/api/users").status_code == 200
    assert check(client, token=token, uri="/api/users/").status_code == 200
    assert check(client, token=token, uri="/api/users/uuid-123").status_code == 200

    # No coinciden por prefijo parcial (segmentos incompletos)
    assert check(client, token=token, uri="/api/usersx").status_code == 403
    assert check(client, token=token, uri="/api/roles_extra").status_code == 403
    assert check(client, token=token, uri="/api/steganography/analyzer").status_code == 403


def test_check_ruta_no_en_mapa_403(client, db, caplog):
    create_user(db, "admin", roles=("ADMIN",))
    token = login(client, "admin").json()["access_token"]

    r = check(client, token=token, uri="/api/desconocida")
    assert r.status_code == 403
    assert r.json() == {
        "subject_id": r.json()["subject_id"],
        "action": "unknown",
        "allowed": False,
        "reason": "unknown_action",
    }
    assert testing.events(caplog, "authz.denied")


def test_jwt_alterado_401(client, db):
    create_user(db, "ana")
    token = login(client, "ana").json()["access_token"]
    head, _, sig = token.split(".")
    forged_body = b64e(b'{"sub":"otro","sid":"otro"}')
    r = check(client, token=f"{head}.{forged_body}.{sig}")
    assert r.status_code == 401
    assert r.json() == {"allowed": False, "reason": "invalid_token"}


def test_jwt_vencido_401(app, client, db):
    create_user(db, "ana")
    login_res = login(client, "ana")
    token = login_res.json()["access_token"]

    # Crear token idéntico pero expirado
    expired_at = datetime.now(UTC) - timedelta(minutes=5)
    claims = jwt.decode(token, options={"verify_signature": False})
    expired_token = app.state.signer.issue(
        user_id=claims["sub"],
        username=claims["name"],
        session_id=claims["sid"],
        roles=claims["roles"],
        expires_at=expired_at,
    )
    r = check(client, token=expired_token)
    assert r.status_code == 401
    assert r.json() == {"allowed": False, "reason": "invalid_token"}


def test_jwt_de_sesion_terminada_401(client, db):
    create_user(db, "ana")
    token = login(client, "ana").json()["access_token"]
    db("UPDATE user_sessions SET ended_at = now(), end_reason = 'logout'")
    r = check(client, token=token)
    assert r.status_code == 401
    assert r.json() == {"allowed": False, "reason": "session_ended"}


def test_cuenta_inactiva_401(client, db):
    create_user(db, "ana")
    token = login(client, "ana").json()["access_token"]
    db("UPDATE users SET status = 'inactive'")
    r = check(client, token=token)
    assert r.status_code == 401
    assert r.json() == {"allowed": False, "reason": "user_inactive"}


def test_solo_cuentan_roles_active(client, db):
    create_user(db, "analista", roles=("ANALYST",))
    token = login(client, "analista").json()["access_token"]

    assert check(client, token=token, uri="/api/steganography/analyze").status_code == 200

    # Desactivar el rol ANALYST
    db("UPDATE roles SET status = 'inactive' WHERE name = 'ANALYST'")

    r = check(client, token=token, uri="/api/steganography/analyze")
    assert r.status_code == 403
    assert r.json()["allowed"] is False
    assert r.json()["reason"] == "no_active_role_grants_permission"


def test_claim_roles_del_jwt_no_autoriza_nada(app, client, db):
    # Cuenta creada sin roles en la BD
    user_id = create_user(db, "ana")
    token = login(client, "ana").json()["access_token"]
    claims = jwt.decode(token, options={"verify_signature": False})

    # Forjar token válido firmado que contenga claim roles=["ADMIN"]
    fake_token = app.state.signer.issue(
        user_id=user_id,
        username="ana",
        session_id=claims["sid"],
        roles=["ADMIN"],
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    # Debe ser denegado porque la BD manda y ana no tiene roles activos en user_roles
    r = check(client, token=fake_token, uri="/api/users")
    assert r.status_code == 403
    assert r.json()["allowed"] is False
    assert r.json()["reason"] == "no_active_role_grants_permission"


def test_r16_check_solo_para_el_gateway(client, db):
    create_user(db, "ana")
    token = login(client, "ana").json()["access_token"]

    # Llamada con token de servicio de stego -> 401 (rechazado por middleware de servicio)
    r_bad_svc = client.post(
        "/internal/authorization/check",
        headers={
            **testing.service_headers("stego"),
            "Authorization": f"Bearer {token}",
            "X-Original-URI": "/api/auth/profile",
        },
    )
    assert r_bad_svc.status_code == 401

    # Llamada sin token de servicio -> 401
    r_no_svc = client.post(
        "/internal/authorization/check",
        headers={
            "X-Service-Token": "",
            "Authorization": f"Bearer {token}",
            "X-Original-URI": "/api/auth/profile",
        },
    )
    assert r_no_svc.status_code == 401

    # Llamada con token de gateway -> 200
    r_gw = check(client, token=token, uri="/api/auth/profile")
    assert r_gw.status_code == 200
