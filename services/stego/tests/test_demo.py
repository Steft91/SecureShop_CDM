"""STG-4: las imágenes de la demo (T09, T10) dan lo esperado contra la API real."""

import subprocess
import sys
from pathlib import Path

import pytest
from conftest import SERVICE_DIR, upload

EXPECTED = {
    "referencia.png": (200, "sin_indicios"),
    "lsb.png": (200, "sospechoso"),
    "zip-al-final.png": (200, "sospechoso"),
    "no-es-imagen.png": (415, None),
    "truncada.png": (422, None),
}


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    folder = tmp_path_factory.mktemp("demo")
    subprocess.run(
        [sys.executable, str(SERVICE_DIR / "tools" / "stego_lab.py"), "demo", str(folder)],
        check=True,
    )
    return folder


@pytest.mark.parametrize(("name", "expected"), EXPECTED.items())
def test_imagen_de_demo(demo, client, name, expected):
    response = upload(client, (demo / name).read_bytes(), name=name)
    status = response.json().get("status") if response.status_code == 200 else None
    assert (response.status_code, status) == expected


def test_lsb_es_la_referencia_con_carga(demo):
    from PIL import Image

    clean = Image.open(demo / "referencia.png")
    altered = Image.open(demo / "lsb.png")
    assert clean.size == altered.size


def test_archivo_grande_para_t10_no_se_versiona(demo):
    assert (demo / "grande.png").stat().st_size > 5 * 1024 * 1024
    ignored = Path(SERVICE_DIR).parents[1] / "docs" / "demo-imagenes" / ".gitignore"
    assert "grande.png" in ignored.read_text(encoding="utf-8")


@pytest.mark.parametrize(("name", "expected"), EXPECTED.items())
def test_imagen_versionada_da_lo_esperado(client, name, expected):
    """Las de docs/demo-imagenes (las que usa Postman), no solo las recién generadas."""
    versioned = Path(SERVICE_DIR).parents[1] / "docs" / "demo-imagenes" / name
    response = upload(client, versioned.read_bytes(), name=name)
    status = response.json().get("status") if response.status_code == 200 else None
    assert (response.status_code, status) == expected
