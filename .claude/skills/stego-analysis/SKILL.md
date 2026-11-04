---
name: stego-analysis
description: Referencia del estegoanálisis del servicio stego (9 formatos de la Actividad 3, chi² de Westfeld, análisis RS, entropía LSB, estructura, veredicto y calibración). Úsala al tocar services/stego, ajustar umbrales o agregar un formato.
---
# Estegoanálisis en `stego` (spec §12)

`stego` no guarda nada: valida el archivo, lo analiza y responde un veredicto.

## Alcance del primer parcial
Manda la spec §23.7. Obligatorio: PNG (píxeles y estructura). JPEG, GIF y WAV entran con lo que ya tienen (STG-1…5); MP3 y MP4 (STG-6) y PDF, DOCX y TXT (STG-7) no bloquean la entrega.

- Cada formato valida firma y tipo declarado, aplica su tope antes de parsear, limita profundidad y recursos, y devuelve `sin_indicios`, `sospechoso`, `no_concluyente` o `error`.
- La firma manda; TXT es la única excepción y requiere extensión `.txt` declarada.
- No se ejecutan macros, multimedia, enlaces ni contenido activo; `stego` no sanitiza.
- Métricas por formato: GIF (paleta y frames), WAV (chunks y LSB en silencio), MP3 (frames e ID3), MP4 (cajas ISO-BMFF), PDF (estructura), DOCX (OOXML) y TXT (invisibles, caracteres de control y entropía).
- El gateway permite 6 MB solo para el análisis (margen del multipart); `stego` corta en 5 MB con 413.

## Veredicto y política (spec §23.7)
| `status` | Cuándo | `action` |
|---|---|---|
| `error` (415 / 422) | Extensión, `Content-Type` o firma no admitidos (415); corrupto, truncado o más de 20 MP (422) | `rechazo` |
| `sospechoso` | Anomalía estructural (datos al final, chunks de texto grandes o desconocidos, metadatos JPEG excesivos) o chi², RS (o entropía, si se activa) sobre el umbral | `cuarentena` |
| `no_concluyente` | Timeout o fallo del análisis, o menos de 1000 píxeles | `advertencia` |
| `sin_indicios` | Nada de lo anterior | `ninguna` |

Más de 5 MB → 413 sin registro. `sospechoso` es un indicio, no una prueba.

## Detectores (PNG, canales RGB)
| Detector | Cálculo | Dispara si |
|---|---|---|
| Chi² (Westfeld–Pfitzmann) | Por canal: pares `(2k, 2k+1)`, `E=(h2k+h2k+1)/2`, `χ²=Σ(h2k−E)²/E` (pares con `E>4`), `p = chi2.sf(χ², pares−1)`; prefijos 10/25/50/100 % (≥ 1000 píxeles) | `p ≥ STEGO_CHI2_P` (0.95) |
| RS (Fridrich 2001) | Grupos 2×2 en zigzag, variación `Σ|xᵢ₊₁−xᵢ|`, máscara `[0,1,1,0]`, raíz de menor módulo de `2(d1+d0)x² + (d−0−d−1−d1−3d0)x + d0−d−0`, `p̂ = x/(x−½)` | `p̂ ≥ STEGO_RS_RATE` (0.08) |
| Entropía LSB | Bloques 64×64; media y fracción de bloques con H ≥ 0.999 | Solo si `STEGO_ENTROPY_TRIGGER` está activo (por defecto, no) |
| Estructura PNG | Bytes tras `IEND`, chunks de texto > 1 KB, chunks desconocidos | Cualquiera |
| Estructura JPEG | Más de 16 bytes tras `FFD9`, APPn+COM > 64 KB | Cualquiera |

## Valores medidos en el prototipo (2026-10-13, imágenes sintéticas "fotográficas")
| Imagen | chi² p | RS p̂ |
|---|---|---|
| Limpia (3 semillas) | 0.33–0.38 | 0.002–0.013 |
| LSB secuencial 5 % | 0.993–0.999 | 0.04–0.05 |
| LSB secuencial 10 % | 0.9994–0.9999 | 0.094–0.098 |
| LSB aleatorio 10 % | 0.59–0.69 | 0.11–0.12 |
| LSB aleatorio 50 % | 0.994–0.998 | 0.51–0.54 |
| LSB aleatorio 100 % | 1.0 | 1.0 (¡0.0 en una semilla: RS degenera cerca del 100 %; lo cubre chi²!) |
| Captura con colores planos | 0.0 | 0.0 |

## Calibración con fotos reales
1. Copia ≥ 30 imágenes limpias (fotos de celular, capturas) en `services/stego/tools/calibracion/` (gitignored). Para el primer parcial alcanzan 15.
2. `python services/stego/tools/stego_lab.py calibrate services/stego/tools/calibracion`
3. Elige umbrales con FPR ≤ 5 % y TPR máxima para "secuencial 10 %". Configúralos con `STEGO_CHI2_P` / `STEGO_RS_RATE` en `deploy/docker-compose.yml` y anota la tabla en `docs/calibracion-estego.md`.

## Agregar un formato
1. Firma + `validate` + `analyze` en `stego_svc/formats.py`, registrado al final de `FORMATS` (PNG y JPEG validan con Pillow vía `pil_format`).
2. Módulo `stego_svc/<formato>.py` con funciones de módulo (las ejecuta un `ProcessPoolExecutor`).
3. Clasificar sus motivos en `stego_svc/verdict.py` (`STRUCTURAL` o `STATISTICAL`).
4. Tests: uno limpio y uno con payload. Actualizar R6/R9 en la trazabilidad.
