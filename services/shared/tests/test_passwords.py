import pytest
from shared.passwords import hash_secret, strong_enough, verify_secret


def test_hash_es_argon2id_con_parametros_rfc9106():
    stored = hash_secret("Clave-Segura-2026")
    assert stored.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert verify_secret(stored, "Clave-Segura-2026")
    assert not verify_secret(stored, "otra-clave")


def test_sin_hash_verifica_contra_dummy_y_siempre_falla():
    assert verify_secret(None, "dummy-password-timing-only") is False
    assert verify_secret(None, "cualquier-cosa") is False


def test_hash_malformado_no_explota():
    assert verify_secret("no-es-un-hash", "x") is False


@pytest.mark.parametrize(
    ("secret", "forbid", "ok"),
    [
        ("Clave-Segura-2026", "", True),
        ("clavesegura2026", "", False),  # 2 clases
        ("Corta-1", "", False),  # < 12
        ("Ana-Lopez-2026", "ana-lopez-2026", False),  # igual al usuario
        ("ÑANDÚ-feliz-99", "", True),
    ],
)
def test_politica_de_claves(secret, forbid, ok):
    assert strong_enough(secret, forbid=forbid) is ok
