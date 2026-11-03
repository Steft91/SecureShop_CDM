"""Análisis estructural acotado de GIF."""
import io
from PIL import Image

def structure(data):
    if not data.startswith((b"GIF87a", b"GIF89a")):
        return {"valid": False, "frames": 0, "trailing_bytes": 0, "comments_bytes": 0}
    position = 6
    if len(data) < 13: return {"valid": False, "frames": 0, "trailing_bytes": 0, "comments_bytes": 0}
    width = int.from_bytes(data[position:position + 2], "little")
    height = int.from_bytes(data[position + 2:position + 4], "little")
    packed = data[position + 4]; position += 7
    if packed & 0x80: position += 3 * (2 ** ((packed & 7) + 1))
    frames, comments = 0, 0
    while position < len(data):
        marker = data[position]; position += 1
        if marker == 0x3B: break
        if marker == 0x2C:
            if position + 9 > len(data): return {"valid": False, "frames": frames, "trailing_bytes": 0, "comments_bytes": comments}
            packed = data[position + 8]; position += 9
            if packed & 0x80: position += 3 * (2 ** ((packed & 7) + 1))
            if position >= len(data): break
            position += 1
            while position < len(data):
                size = data[position]; position += 1
                if size == 0: break
                position += size
            frames += 1
        elif marker == 0x21:
            if position >= len(data): break
            label = data[position]; position += 1
            total = 0
            while position < len(data):
                size = data[position]; position += 1
                if size == 0: break
                total += size; position += size
            if label == 0xFE: comments += total
        else:
            return {"valid": False, "frames": frames, "trailing_bytes": 0, "comments_bytes": comments}
    trailer = data.rfind(b"\x3b") + 1
    return {"valid": frames > 0 and trailer > 0, "frames": frames, "width": width, "height": height, "trailing_bytes": max(0, len(data) - trailer), "comments_bytes": comments}

def structural_reasons(found):
    reasons = []
    if not found.get("valid"): reasons.append("GIF inválido o truncado")
    if found.get("frames", 0) > 100: reasons.append("demasiados frames")
    if found.get("comments_bytes", 0) > 1024: reasons.append("comentarios excesivos")
    if found.get("trailing_bytes", 0): reasons.append("datos después del trailer GIF")
    return reasons

def analyze(data, cfg):
    found = structure(data); reasons = structural_reasons(found)
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > cfg.get("max_pixels", 20_000_000): reasons.append("demasiados píxeles")
    except Exception:
        if "GIF inválido o truncado" not in reasons: reasons.append("GIF inválido o truncado")
    return {"suspicious": bool(reasons), "reasons": reasons, "metrics": found}
