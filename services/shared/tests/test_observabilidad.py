import io
import json
import logging
import re

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from test_r16_service_auth import build_app

from shared import audit, testing
from shared.identity import require_gateway
from shared.observability import REQUEST_HEADER, REQUEST_ID, JsonFormatter


def build_client() -> TestClient:
    app = build_app()

    @app.get("/api/eco", dependencies=[Depends(require_gateway)])
    async def eco() -> dict:
        audit.emit("info", "prueba.eco", actor="system")
        return {"id": REQUEST_ID.get()}

    return TestClient(app, base_url=testing.ORIGIN)


def test_el_id_del_gateway_llega_al_codigo_y_a_los_eventos():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    # formatea dentro de la petición, como en producción
    handler.setFormatter(JsonFormatter("auth"))
    logging.getLogger("audit").addHandler(handler)
    try:
        headers = {**testing.gateway_headers(), REQUEST_HEADER: "0123456789abcdef"}
        assert build_client().get("/api/eco", headers=headers).json() == {"id": "0123456789abcdef"}
    finally:
        logging.getLogger("audit").removeHandler(handler)
    line = json.loads(stream.getvalue())
    assert (line["msg"], line["request_id"]) == ("prueba.eco", "0123456789abcdef")
    assert line["event"]["actor"] == "system"


@pytest.mark.parametrize("presented", [None, "corto", "con espacios y !!"])
def test_id_ausente_o_invalido_se_reemplaza(presented):
    headers = {**testing.gateway_headers(), **({REQUEST_HEADER: presented} if presented else {})}
    got = build_client().get("/api/eco", headers=headers).json()["id"]
    assert re.fullmatch(r"[0-9a-f]{32}", got)


def test_formato_json_de_los_registros():
    record = logging.LogRecord("http", logging.INFO, __file__, 1, "request", None, None)
    record.status, record.ms = 200, 3
    token = REQUEST_ID.set("0123456789abcdef")
    try:
        line = json.loads(JsonFormatter("auth").format(record))
    finally:
        REQUEST_ID.reset(token)
    assert (line["service"], line["level"], line["request_id"], line["msg"]) == (
        "auth",
        "info",
        "0123456789abcdef",
        "request",
    )
    assert (line["status"], line["ms"]) == (200, 3)


def test_error_500_se_registra_con_el_id():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter("auth"))
    logging.getLogger("http").addHandler(handler)
    try:
        client = TestClient(build_app(), base_url=testing.ORIGIN, raise_server_exceptions=False)
        headers = {**testing.gateway_headers(), REQUEST_HEADER: "0123456789abcdef"}
        assert client.get("/api/falla", headers=headers).status_code == 500
    finally:
        logging.getLogger("http").removeHandler(handler)
    [line] = [json.loads(raw) for raw in stream.getvalue().splitlines() if '"exc"' in raw]
    assert line["request_id"] == "0123456789abcdef"


def test_una_linea_por_peticion_sin_query_string(caplog):
    with caplog.at_level(logging.INFO, logger="http"):
        build_client().get("/api/eco?token=secreto", headers=testing.gateway_headers())
    [record] = [r for r in caplog.records if r.name == "http"]
    assert (record.method, record.path, record.status) == ("GET", "/api/eco", 200)
    assert "secreto" not in caplog.text
