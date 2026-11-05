"""JPEG, GIF y WAV entran con análisis estructural (spec §23.1): structure_analysis."""

import io
import wave

from conftest import upload
from PIL import Image

from stego_svc import jpeg
from stego_svc.synthetic import jpeg_bytes, natural_image

JPEG = jpeg_bytes(natural_image(0, 128))


def wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 800)
    return buffer.getvalue()


def test_jpeg_limpio_sin_indicios_con_analisis_estructural(client):
    body = upload(client, JPEG, name="foto.jpg", ctype="image/jpeg").json()
    assert (body["status"], body["technique"]) == ("sin_indicios", "structure_analysis")
    assert body["indicators"]["trailing_bytes"] == 0


def test_jpeg_con_datos_tras_eoi_es_sospechoso(client):
    body = upload(client, JPEG + b"x" * 64, name="foto.jpeg", ctype="image/jpeg").json()
    assert body["status"] == "sospechoso"
    assert "datos después de EOI" in body["reasons"]


def test_jpeg_con_metadatos_excesivos():
    found = jpeg.structure(JPEG)
    assert jpeg.structural_reasons({**found, "metadata_bytes": 70_000}) == ["metadatos excesivos"]


def test_jpeg_con_comentario_cuenta_metadatos():
    buffer = io.BytesIO()
    Image.open(io.BytesIO(JPEG)).save(buffer, format="JPEG", comment=b"c" * 500)
    assert jpeg.structure(buffer.getvalue())["metadata_bytes"] >= 500


def test_wav_valido_y_wav_con_cola(client):
    clean = upload(client, wav_bytes(), name="audio.wav", ctype="audio/wav").json()
    assert clean["status"] == "sin_indicios"
    tail = upload(client, wav_bytes() + b"oculto", name="audio.wav", ctype="audio/x-wav").json()
    assert tail["status"] == "sospechoso"


def test_gif_por_la_api(client):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="GIF")
    body = upload(client, buffer.getvalue(), name="a.gif", ctype="image/gif").json()
    assert (body["status"], body["mime"]) == ("sin_indicios", "image/gif")


def test_r09_contenido_que_no_coincide_con_la_firma(client):
    """La firma manda: un JPEG con extensión .png y Content-Type image/png no pasa."""
    assert upload(client, JPEG, name="foto.png", ctype="image/png").status_code == 415
