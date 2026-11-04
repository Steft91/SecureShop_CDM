"""Clasificación estable de resultados de análisis."""
def classify(result):
    reasons = result.get("reasons", [])
    if any(r in reasons for r in ("datos después de IEND", "datos después de EOI", "chunks de texto grandes", "chunks desconocidos", "metadatos excesivos", "GIF inválido o truncado", "RIFF/WAVE inválido o truncado")):
        return "problema"
    return "revision_manual" if result.get("suspicious") else "limpia"
