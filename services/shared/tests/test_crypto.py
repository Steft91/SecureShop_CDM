import pytest

from shared.crypto import b64d, b64e, new_token, sha256, token_hash


def test_base64url_ida_y_vuelta_sin_relleno():
    data = bytes(range(256))
    text = b64e(data)
    assert "=" not in text and "+" not in text and "/" not in text
    assert b64d(text) == data


@pytest.mark.parametrize("text", ["QU!!JD", "ab+/", "QUJD=", "A"])
def test_base64url_rechaza_texto_que_no_lo_es(text):
    with pytest.raises(ValueError):
        b64d(text)


def test_tokens_aleatorios_y_su_hash():
    a, b = new_token(), new_token()
    assert a != b
    assert len(b64d(a)) == 32
    assert token_hash(a) == sha256(a.encode())
    assert len(token_hash(a)) == 32
