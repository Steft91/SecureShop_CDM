from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect

from shared import testing
from shared.identity import (
    UserIdentity,
    require_gateway,
    require_perm,
    require_user,
    user_from_headers,
)
from shared.service_auth import allow
from shared.web import create_base_app


class Body(BaseModel):
    n: int


def build_app():
    app = create_base_app(
        title="prueba",
        settings=SimpleNamespace(allowed_origins=frozenset({testing.ORIGIN})),
        engine=create_async_engine("postgresql+asyncpg://nadie@127.0.0.1:1/nada"),  # no se usa
        service_auth=testing.service_auth("auth", ("gateway", "stego")),
    )
    router = APIRouter()

    @router.post("/api/publico", dependencies=[Depends(require_gateway)])
    async def publico(body: Body) -> dict:
        return {"n": body.n}

    @router.get("/api/admin/x")
    async def admin(who: UserIdentity = Depends(require_perm("roles:manage"))) -> dict:
        return {"user": who.username}

    @router.get("/api/yo")
    async def yo(who: UserIdentity = Depends(require_user)) -> dict:
        return {
            "user_id": who.user_id,
            "username": who.username,
            "session_id": who.session_id,
            "perms": sorted(who.perms),
        }

    @router.post("/internal/solo-gateway", dependencies=[Depends(allow("gateway"))])
    async def interno() -> dict:
        return {"ok": True}

    @router.get("/api/falla", dependencies=[Depends(require_gateway)])
    async def falla() -> dict:
        raise RuntimeError("boom")

    app.include_router(router)
    return app


@pytest.fixture
def client():
    return TestClient(build_app(), base_url=testing.ORIGIN, raise_server_exceptions=False)


def test_sin_token_401_y_se_registra(client, caplog):
    r = client.post("/api/publico", json={"n": 1})
    assert r.status_code == 401
    assert r.json() == {"error": "no autorizado"}
    [event] = testing.events(caplog, "svc.reject.token")
    assert (event["target"], event["severity"]) == ("/api/publico", "warning")


def test_token_desconocido_401(client):
    assert client.get("/api/admin/x", headers={"X-Service-Token": "inventado"}).status_code == 401


def test_ruta_publica_solo_desde_el_gateway(client, caplog):
    r = client.post("/api/publico", json={"n": 1}, headers=testing.service_headers("stego"))
    assert r.status_code == 403
    assert testing.events(caplog, "svc.reject.token")[0]["actor"] == "svc:stego"


def test_csrf_rechaza_origin_ajeno(client, caplog):
    ajeno = {"X-Service-Token": testing.TOKENS["gateway"], "origin": "https://evil.example"}
    assert client.post("/api/publico", json={"n": 1}, headers=ajeno).status_code == 403
    assert testing.events(caplog, "http.reject.origin")
    r = client.post("/api/publico", json={"n": 2}, headers=testing.gateway_headers())
    assert r.json() == {"n": 2}


def test_sin_origin_pasa_porque_no_hay_cookies(client):
    # Postman, curl e Insomnia no mandan Origin; sin cookies no hay CSRF (spec §23.1).
    sin_origin = {"X-Service-Token": testing.TOKENS["gateway"]}
    assert client.post("/api/publico", json={"n": 3}, headers=sin_origin).json() == {"n": 3}


def test_ruta_interna_respeta_la_allowlist(client):
    otro = testing.service_headers("stego")
    assert client.post("/internal/solo-gateway", headers=otro).status_code == 403
    assert (
        client.post("/internal/solo-gateway", headers=testing.gateway_headers()).status_code == 200
    )


def test_identidad_solo_vale_si_la_trae_el_gateway(client):
    assert client.get("/api/admin/x", headers=testing.gateway_headers()).status_code == 401
    ok = client.get("/api/admin/x", headers=testing.user_headers(perms=("roles:manage",)))
    assert ok.json() == {"user": "ana"}
    impostor = {
        **testing.service_headers("stego"),
        "X-User-Id": "x",
        "X-User-Name": "ana",
        "X-Session-Id": "s",
        "X-User-Perms": "roles:manage",
    }
    assert client.get("/api/admin/x", headers=impostor).status_code == 403


def test_r05_sin_el_permiso_403_y_se_registra(client, caplog):
    r = client.get("/api/admin/x", headers=testing.user_headers(perms=("stego:analyze",)))
    assert (r.status_code, r.json()) == (403, {"error": "permiso insuficiente"})
    [event] = testing.events(caplog, "perm.denied")
    assert event["actor"] == "user:ana"
    assert event["details"] == {"required": ["roles:manage"]}


def test_permisos_se_leen_de_la_cabecera(client):
    headers = testing.user_headers(perms=("stego:analyze", "roles:manage"))
    assert client.get("/api/yo", headers=headers).json() == {
        "user_id": testing.USER_ID,
        "username": "ana",
        "session_id": testing.SESSION_ID,
        "perms": ["roles:manage", "stego:analyze"],
    }
    assert client.get("/api/yo", headers=testing.user_headers()).json()["perms"] == []


def test_health_sin_token_y_503_si_la_bd_no_responde(client):
    r = client.get("/health")  # el engine de build_app apunta a un puerto cerrado
    assert (r.status_code, r.json()) == (503, {"error": "bd no disponible"})
    sin_bd = create_base_app(title="sin-bd", settings=None, engine=None, service_auth=None)
    assert TestClient(sin_bd).get("/health").json() == {"status": "ok"}
    assert client.post("/health").status_code == 401  # solo GET /health se libra del token


def test_identidad_ignorada_si_no_la_trae_el_gateway():
    headers = [(b"x-user-id", b"x"), (b"x-user-name", b"admin"), (b"x-session-id", b"s")]
    scope = {"type": "http", "headers": headers, "state": {"caller": "stego"}}
    assert user_from_headers(Request(scope)) is None
    scope["state"]["caller"] = "gateway"
    assert user_from_headers(Request(scope)).username == "admin"


def test_websocket_sin_token_se_rechaza(caplog):
    app = build_app()

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.close()

    client = TestClient(app, base_url=testing.ORIGIN)
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws"):
        pass
    assert testing.events(caplog, "svc.reject.token")
    with client.websocket_connect("/ws", headers=testing.service_headers("gateway")):
        pass


def test_errores_genericos(client):
    assert client.get("/api/falla", headers=testing.gateway_headers()).json() == {
        "error": "error interno"
    }
    r = client.post("/api/publico", json={"n": "x"}, headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (422, {"error": "datos inválidos"})
