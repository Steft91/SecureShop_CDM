# Stego analysis

## Alcance del primer parcial

Analiza los 9 formatos de la Actividad 3: PNG, JPEG, GIF, WAV, MP3, MP4, PDF, DOCX y TXT. Cada formato debe validar firma y tipo declarado, aplicar su tope antes de parsear, limitar profundidad/recursos y devolver `invalida`, `problema`, `revision_manual` o `limpia`.

## Reglas

- La firma manda; TXT es la única excepción y requiere extensión `.txt` declarada.
- No ejecutar macros, multimedia, enlaces ni contenido activo; no sanitizar en `stego`.
- Mantener `validate(data, max_pixels)` y `analyze(data, cfg)` como interfaz y registrar el formato al final de `FORMATS`.
- Usar análisis estructural y métricas específicas: GIF (paleta/frames), WAV (chunks y LSB en silencio), MP3 (frames/ID3), MP4 (ISO-BMFF), PDF (estructura), DOCX (OOXML) y TXT (invisibles/control/entropía).
- El gateway permite 20 MB solo para análisis; los topes específicos siguen aplicándose en `stego`.
