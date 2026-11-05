"""Hallazgos de la auditoría de STG-3: entradas raras que no deben perder el registro ni romper el servicio."""

import os
import zlib
from pathlib import Path

import pytest
from conftest import CLEAN, LSB, analyst, upload

from shared import testing
from stego_svc import pipeline
from stego_svc.config import Settings


def _with_chunk(data: bytes, kind: bytes, body: bytes) -> bytes:
    chunk = len(body).to_bytes(4, "big") + kind + body + zlib.crc32(kind + body).to_bytes(4, "big")
    return data[:-12] + chunk + data[-12:]  # justo antes de IEND


def test_r09_chunk_con_nul_se_registra(client):
    response = upload(client, _with_chunk(CLEAN, b"\x00abc", b"oculto"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sospechoso"
    assert body["indicators"]["unknown_chunks"] == ["00616263"]


def test_wav_con_id_nul_se_registra(client):
    fmt = b"fmt " + (16).to_bytes(4, "little") + bytes.fromhex("01000100401f0000803e000002001000")
    data = b"data" + (4).to_bytes(4, "little") + b"\x00\x00\x00\x00"
    odd = b"\x00\x00\x00\x00" + (2).to_bytes(4, "little") + b"xx"
    body = b"WAVE" + fmt + odd + data
    wav = b"RIFF" + len(body).to_bytes(4, "little") + body
    response = upload(client, wav, name="audio.wav", ctype="audio/wav")
    assert response.status_code == 200, response.text
    assert "00000000" in response.json()["indicators"]["chunks"]


def test_falla_al_persistir_emite_evento(make_client, caplog):
    client = make_client(url=testing.dsn("stego_app", "x", "stego_test").replace("5433", "1"))
    assert upload(client, LSB).status_code == 503
    (event,) = testing.events(caplog, "stego.persist_failed")
    assert event["severity"] == "critical"
    assert set(event["details"]) == {"analysis_id", "sha256", "status"}


def test_pool_roto_se_recrea(make_client):
    client = make_client()
    with pytest.raises(Exception):  # noqa: B017 - el worker muere y el pool queda roto
        client.app.state.pool.submit(os._exit, 1).result()
    assert upload(client, CLEAN).json()["status"] == "no_concluyente"
    assert upload(client, CLEAN).json()["status"] == "sin_indicios"


def test_cuarentena_parcial_no_deja_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline.os, "fdopen", lambda fd, mode: _Broken(fd))
    with pytest.raises(OSError):
        pipeline.quarantine(str(tmp_path), "00000000-0000-4000-8000-0000000000aa", LSB)
    assert not list(Path(tmp_path).iterdir())


class _Broken:
    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.fd)

    def write(self, _):
        raise OSError("disco lleno")


def test_uuid_en_formato_urn_da_404_y_no_503(client):
    urn = "urn:uuid:00000000-0000-4000-8000-0000000000ff"
    response = client.get(f"/api/steganography/results/{urn}", headers=analyst())
    assert response.status_code == 404


@pytest.mark.parametrize("field", ["stego_chi2_p", "stego_rs_rate", "stego_entropy_trigger"])
@pytest.mark.parametrize("value", [float("nan"), 0.0, 1.5])
def test_umbral_invalido_no_arranca(field, value):
    with pytest.raises(ValueError):
        Settings(database_url="postgresql+asyncpg://x", **{field: value})
