"""R5 y R16: solo el gateway llama, con identidad y con el permiso del catálogo."""

from conftest import CLEAN, upload

from shared import testing


def test_sin_token_del_gateway_401(client):
    response = client.post(
        "/api/steganography/analyze", files={"file": ("a.png", CLEAN, "image/png")}
    )
    assert response.status_code == 401


def test_sin_identidad_del_gateway_401(client):
    response = upload(client, CLEAN, headers=testing.gateway_headers())
    assert response.status_code == 401


def test_r05_sin_el_permiso_403(client, caplog):
    headers = testing.user_headers(perms=("steganography.results.read",))
    response = upload(client, CLEAN, headers=headers)
    assert response.status_code == 403
    assert testing.events(caplog, "perm.denied")


def test_permisos_de_otro_llamador_se_ignoran(make_client):
    """Un servicio que no es el gateway no puede inyectar X-User-*: el middleware lo corta."""
    client = make_client()
    headers = {**testing.user_headers(perms=("steganography.analyze",))}
    headers["X-Service-Token"] = "token-falso"
    assert upload(client, CLEAN, headers=headers).status_code == 401


def test_ruta_vieja_ya_no_existe(client):
    response = client.post(
        "/api/stego/analyze",
        headers=testing.user_headers(perms=("steganography.analyze",)),
        files={"file": ("a.png", CLEAN, "image/png")},
    )
    assert response.status_code == 404


def test_health(client):
    """/health no exige token de servicio: lo usa el healthcheck de Docker."""
    assert client.get("/health").json() == {"status": "ok"}


def test_health_sin_bd(make_client):
    client = make_client(url=testing.dsn("stego_app", "x", "stego_test").replace("5433", "1"))
    assert client.get("/health").status_code == 503
