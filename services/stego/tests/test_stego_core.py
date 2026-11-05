import io
from pathlib import Path

from PIL import Image

from stego_svc import formats
from stego_svc.synthetic import embed_lsb, natural_image, png_bytes
from stego_svc.verdict import classify

CFG = {"chi2_p": 0.995, "rs_rate": 0.15, "entropy_trigger": None}


def test_imagen_limpia_es_sin_indicios_o_sospechosa():
    result = formats.FORMATS["image/png"].analyze(png_bytes(natural_image(0)), CFG)
    assert classify(result) in {"sin_indicios", "sospechoso"}


def test_lsb_secuencial_es_sospechoso():
    data = png_bytes(embed_lsb(natural_image(0), 0.10, "seq"))
    result = formats.FORMATS["image/png"].analyze(data, CFG)
    assert classify(result) == "sospechoso"


def test_firma_invalida():
    kind, reasons = formats.validate(b"no es una imagen")
    assert kind is None
    assert reasons


def test_limite_de_pixeles():
    image = Image.new("RGB", (20, 20), "white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    kind, reasons = formats.validate(buf.getvalue(), max_pixels=10)
    assert kind is None
    assert "demasiados píxeles" in reasons


def test_archivo_demo_invalido():
    path = Path("docs/demo-imagenes/no-es-imagen.png")
    if path.exists():
        assert formats.validate(path.read_bytes())[0] is None
