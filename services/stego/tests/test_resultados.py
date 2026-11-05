"""GET /api/steganography/results/{id}: RBAC y propiedad del recurso (T11)."""

from conftest import CLEAN, OTHER_ID, analyst, upload

from shared import testing


def results(client, analysis_id, headers):
    return client.get(f"/api/steganography/results/{analysis_id}", headers=headers)


def test_el_dueno_lee_su_analisis(client, caplog):
    created = upload(client, CLEAN).json()
    response = results(client, created["analysis_id"], analyst())
    assert response.status_code == 200
    assert response.json() == created
    assert testing.events(caplog, "stego.result.read")


def test_r05_resultado_ajeno_403(client, caplog):
    created = upload(client, CLEAN).json()
    response = results(client, created["analysis_id"], analyst(user_id=OTHER_ID))
    assert response.status_code == 403
    assert testing.events(caplog, "perm.denied")


def test_read_any_lee_el_analisis_ajeno(client):
    created = upload(client, CLEAN).json()
    headers = analyst(user_id=OTHER_ID, extra=("steganography.results.read_any",))
    assert results(client, created["analysis_id"], headers).status_code == 200


def test_inexistente_404(client):
    missing = "00000000-0000-4000-8000-0000000000ff"
    assert results(client, missing, analyst()).status_code == 404
    assert results(client, "no-es-un-uuid", analyst()).status_code == 404


def test_sin_permiso_de_lectura_403(client):
    created = upload(client, CLEAN).json()
    headers = testing.user_headers(perms=("steganography.analyze",))
    assert results(client, created["analysis_id"], headers).status_code == 403
