"""Punto de extensión de formatos aceptados."""
from dataclasses import dataclass
from PIL import Image
from stego_svc import gif, jpeg, png, wav

@dataclass(frozen=True)
class Format:
    mime: str
    extensions: tuple[str, ...]
    signature: bytes
    analyze: object

FORMATS = {
    "image/png": Format("image/png", (".png",), b"\x89PNG\r\n\x1a\n", png.analyze),
    "image/jpeg": Format("image/jpeg", (".jpg", ".jpeg"), b"\xff\xd8\xff", jpeg.analyze),
    "image/gif": Format("image/gif", (".gif",), b"GIF", gif.analyze),
    "audio/wav": Format("audio/wav", (".wav",), b"RIFF", wav.analyze),
}

def validate(data, max_bytes=5 * 1024 * 1024, max_pixels=20_000_000):
    reasons = []
    if len(data) > max_bytes: reasons.append("archivo demasiado grande")
    kind = next((mime for mime, fmt in FORMATS.items() if data.startswith(fmt.signature)), None)
    if kind == "audio/wav" and (len(data) < 12 or data[8:12] != b"WAVE"):
        kind = None
    if not kind: return None, ["firma o formato inválido"] + reasons
    try:
        if kind in ("image/png", "image/jpeg", "image/gif"):
            with Image.open(__import__("io").BytesIO(data)) as image:
                if image.width * image.height > max_pixels: reasons.append("demasiados píxeles")
                image.verify()
    except Exception:
        reasons.append("archivo truncado o no decodificable")
    return (kind if not reasons else None), reasons
