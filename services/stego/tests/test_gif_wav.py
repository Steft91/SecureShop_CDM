import io
import wave

from PIL import Image

from stego_svc import formats, gif
from stego_svc.verdict import classify


def gif_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="GIF")
    return buffer.getvalue()


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 80)
    return buffer.getvalue()


def test_gif_valido():
    data = gif_bytes()
    kind, reasons = formats.validate(data)
    assert kind == "image/gif"
    assert reasons == []
    result = formats.FORMATS[kind].analyze(data, {"max_pixels": 20_000_000})
    assert classify(result) == "sin_indicios"


def test_gif_truncado_es_invalido():
    kind, reasons = formats.validate(gif_bytes()[:-4])
    assert kind is None
    assert reasons


def test_wav_valido():
    data = wav_bytes()
    kind, reasons = formats.validate(data)
    assert kind == "audio/wav"
    assert reasons == []
    result = formats.FORMATS[kind].analyze(data, {})
    assert classify(result) == "sin_indicios"


def test_wav_truncado_es_invalido():
    kind, reasons = formats.validate(wav_bytes()[:-10])
    assert kind is None
    assert reasons


def test_gif_con_datos_tras_el_trailer_aunque_contengan_punto_y_coma():
    """El final es el trailer que encuentra el parser, no el último ';' del archivo."""
    found = gif.structure(gif_bytes() + b"oculto;mas")
    assert found["trailing_bytes"] == len(b"oculto;mas")
    assert "datos después del trailer GIF" in gif.structural_reasons(found)
