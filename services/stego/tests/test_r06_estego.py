"""Criterios de STG-1 y STG-2 sobre los detectores, con los umbrales de producción."""

import io
import json

import numpy as np
import pytest
from conftest import upload
from PIL import Image

from stego_svc import jpeg, png, stego, synthetic

CFG = {"chi2_p": 0.995, "rs_rate": 0.15, "entropy_trigger": None}


def test_r06_lsb_aleatorio_al_50_dispara_rs():
    pixels = synthetic.embed_lsb(synthetic.natural_image(1), 0.50, "random")
    assert max(stego.rs_estimate(pixels[..., c]) for c in range(3)) >= CFG["rs_rate"]


def test_captura_con_colores_planos_no_dispara():
    flat = np.full((200, 300, 3), 245, np.uint8)
    flat[40:80, 30:270] = (30, 90, 200)
    assert png.analyze(synthetic.png_bytes(flat), CFG)["suspicious"] is False


def test_las_metricas_se_serializan_sin_nan():
    flat = np.full((64, 64, 3), 200, np.uint8)
    json.dumps(png.analyze(synthetic.png_bytes(flat), CFG), allow_nan=False)  # no lanza


def test_jpeg_progresivo_no_confunde_al_parser():
    buffer = io.BytesIO()
    Image.fromarray(synthetic.natural_image(0, 128)).save(buffer, format="JPEG", progressive=True)
    data = buffer.getvalue()
    assert jpeg.structure(data)["trailing_bytes"] == 0
    assert jpeg.analyze(data, CFG)["suspicious"] is False
    assert jpeg.analyze(data + b"SECRETO" * 10, CFG)["reasons"] == ["datos después de EOI"]


def test_imagenes_sinteticas_deterministas():
    assert np.array_equal(synthetic.natural_image(3), synthetic.natural_image(3))
    base = synthetic.natural_image(3)
    assert np.array_equal(
        synthetic.embed_lsb(base, 0.3, "random"), synthetic.embed_lsb(base, 0.3, "random")
    )


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.parametrize("mode", ["RGBA", "P", "L", "I;16"])
def test_modos_de_imagen_no_rgb(make_client, mode):
    base = synthetic.natural_image(0, 64)
    images = {
        "RGBA": Image.fromarray(np.dstack([base, np.full((64, 64), 128, np.uint8)])),
        "P": Image.fromarray(base).convert("P"),
        "L": Image.fromarray(base).convert("L"),
        "I;16": Image.fromarray(base[..., 0].astype(np.uint16) * 257),
    }
    response = upload(make_client(), _png(images[mode]))
    assert response.status_code == 200, response.text
    assert response.json()["status"] in {"sin_indicios", "sospechoso", "no_concluyente"}
