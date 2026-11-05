from fastapi.testclient import TestClient

from stego_svc.main import create_app
from stego_svc.config import Settings
from stego_svc.synthetic import natural_image, png_bytes
from shared import testing


def client():
    return TestClient(create_app(Settings(analyze_per_min=10), service_auth=testing.service_auth("stego", ("gateway",))))


def headers(user="api-test", permission="stego:analyze"):
    result = {"X-User-Id": user, "X-Service-Token": testing.TOKENS["gateway"]}
    if permission:
        result["X-User-Perms"] = "steganography.analyze" if permission else ""
    return result


def image_file():
    return {"file": ("clean.png", png_bytes(natural_image(20, 64)), "image/png")}


def test_health_no_requiere_identidad():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_rechaza_peticion_sin_identidad():
    response = client().post("/api/steganography/analyze", files=image_file())
    assert response.status_code == 401


def test_api_rechaza_usuario_sin_permiso():
    response = client().post("/api/steganography/analyze", headers=headers(permission=""), files=image_file())
    assert response.status_code == 403


def test_api_analiza_archivo_y_devuelve_sha256():
    response = client().post("/api/steganography/analyze", headers=headers(), files=image_file())
    assert response.status_code == 200
    body = response.json()
    assert body["mime"] == "image/png"
    assert body["verdict"] in {"limpia", "revision_manual"}
    assert len(body["sha256"]) == 64


def test_api_rechaza_archivo_invalido():
    files = {"file": ("bad.png", b"no es una imagen", "image/png")}
    response = client().post("/api/steganography/analyze", headers=headers(), files=files)
    assert response.status_code == 422


def test_api_aplica_rate_limit_por_usuario():
    test_client = client()
    for _ in range(10):
        response = test_client.post("/api/steganography/analyze", headers=headers("limit-test"), files=image_file())
        assert response.status_code == 200
    response = test_client.post("/api/steganography/analyze", headers=headers("limit-test"), files=image_file())
    assert response.status_code == 429
