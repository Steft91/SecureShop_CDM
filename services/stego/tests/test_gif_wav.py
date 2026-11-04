import io
import struct
import wave

from PIL import Image

from stego_svc import formats
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
    assert classify(result) == "limpia"


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
    assert classify(result) == "limpia"


def test_wav_truncado_es_invalido():
    kind, reasons = formats.validate(wav_bytes()[:-10])
    assert kind is None
    assert reasons
