"""POST /api/steganography/analyze (spec §23.7): validación, veredicto, política y registro."""

import io
import os
from pathlib import Path

from conftest import CLEAN, LSB, ZIP_AT_END, analyst, upload
from PIL import Image

from shared import testing
from stego_svc import pipeline

KEYS = {
    "analysis_id",
    "user_id",
    "filename",
    "sha256",
    "mime",
    "technique",
    "status",
    "indicators",
    "reasons",
    "action",
    "limitations",
    "created_at",
}


def row(db, analysis_id):
    rows = db("SELECT * FROM analyses WHERE id = CAST(:id AS uuid)", id=analysis_id)
    return rows[0] if rows else None


def test_imagen_limpia_sin_indicios(client, db, tmp_path):
    response = upload(client, CLEAN)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == KEYS
    assert (body["status"], body["action"]) == ("sin_indicios", "ninguna")
    assert body["technique"] == "lsb_statistical_analysis"
    assert body["user_id"] == testing.USER_ID
    assert body["indicators"]["chi2_p_threshold"] == 0.995
    saved = row(db, body["analysis_id"])
    assert saved["sha256"].strip() == body["sha256"] and saved["status"] == "sin_indicios"
    assert str(saved["user_id"]) == testing.USER_ID
    assert not list(tmp_path.iterdir())  # sin indicios: el archivo se descarta


def test_r06_imagen_con_lsb_es_sospechoso(client, db, tmp_path):
    body = upload(client, LSB).json()
    assert (body["status"], body["action"]) == ("sospechoso", "cuarentena")
    quarantined = tmp_path / body["analysis_id"]
    assert quarantined.read_bytes() == LSB
    if os.name == "posix":
        assert quarantined.stat().st_mode & 0o777 == 0o600
    assert row(db, body["analysis_id"])["action"] == "cuarentena"


def test_r06_archivo_pegado_al_final_es_sospechoso(client):
    body = upload(client, ZIP_AT_END).json()
    assert body["status"] == "sospechoso"
    assert "datos después de IEND" in body["reasons"]
    assert body["indicators"]["trailing_bytes"] > 0


def test_r09_archivo_que_no_es_imagen_415(client, db, caplog):
    response = upload(client, b"MZ esto es un ejecutable")
    assert response.status_code == 415
    body = response.json()
    assert body["error"] == "formato no admitido"
    saved = row(db, body["analysis_id"])
    assert (saved["status"], saved["action"], saved["technique"]) == (
        "error",
        "rechazo",
        "file_validation",
    )
    assert saved["mime"] is None
    assert testing.events(caplog, "stego.rejected")


def test_extension_que_no_coincide_415(client):
    assert upload(client, CLEAN, name="foto.jpg").status_code == 415


def test_content_type_que_no_coincide_415(client):
    assert upload(client, CLEAN, ctype="image/jpeg").status_code == 415


def test_png_truncado_422(client, db):
    response = upload(client, CLEAN[: len(CLEAN) // 2])
    assert response.status_code == 422
    assert row(db, response.json()["analysis_id"])["status"] == "error"


def test_r09_bomba_de_descompresion_rechazada(make_client):
    client = make_client(max_image_pixels=100)
    assert upload(client, CLEAN).status_code == 422


def test_r10_mas_de_5_mb_413(make_client, db, caplog):
    client = make_client(upload_max_bytes=1000)
    response = upload(client, CLEAN)
    assert response.status_code == 413
    assert response.json() == {"error": "archivo demasiado grande"}
    assert db("SELECT count(*) AS n FROM analyses") == [{"n": 0}]
    assert testing.events(caplog, "stego.rejected")


def test_nombre_largo_se_trunca(client, db):
    body = upload(client, CLEAN, name="a" * 296 + ".png").json()
    assert len(body["filename"]) == 255
    assert len(row(db, body["analysis_id"])["filename"]) == 255


def test_nombre_con_ruta_se_queda_en_el_basename(client):
    body = upload(client, CLEAN, name="..\\..\\etc/foto.png").json()
    assert body["filename"] == "foto.png"


def test_nombre_sin_caracteres_de_control_y_en_nfc():
    # httpx codifica los caracteres de control del multipart; la función se prueba directo.
    assert pipeline.clean_name("../fo\x07to\x00.png") == "foto.png"
    assert pipeline.clean_name("café.png") == "café.png"
    assert pipeline.clean_name(None) == ""


def test_timeout_del_analisis_es_no_concluyente(make_client):
    client = make_client(stego_timeout_s=0)
    body = upload(client, CLEAN).json()
    assert (body["status"], body["action"]) == ("no_concluyente", "advertencia")


def test_imagen_pequena_es_no_concluyente(client):
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")
    body = upload(client, buffer.getvalue()).json()
    assert body["status"] == "no_concluyente"
    assert body["indicators"]["chi2_p"] is None


def test_r10_limite_de_analisis_por_minuto(make_client, caplog):
    client = make_client(analyze_per_min=2)
    assert upload(client, CLEAN).status_code == 200
    assert upload(client, CLEAN).status_code == 200
    assert upload(client, CLEAN).status_code == 429
    assert testing.events(caplog, "stego.ratelimited")
    other = analyst(user_id="00000000-0000-4000-8000-0000000000c3")
    assert upload(client, CLEAN, headers=other).status_code == 200


def test_bd_caida_503_y_sin_archivo_huerfano(make_client, tmp_path):
    client = make_client(url=testing.dsn("stego_app", "x", "stego_test").replace("5433", "1"))
    response = upload(client, LSB)
    assert response.status_code == 503
    assert not list(Path(tmp_path).iterdir())


def test_eventos_sin_nombre_ni_contenido(client, caplog):
    upload(client, CLEAN, name="secreto-del-usuario.png")
    (event,) = testing.events(caplog, "stego.analyzed")
    assert event["severity"] == "info"
    assert set(event["details"]) == {"analysis_id", "sha256", "status", "action"}
    assert "secreto-del-usuario" not in str(event)
