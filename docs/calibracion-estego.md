# Calibración del estegoanálisis

Este documento se completa ejecutando el laboratorio con imágenes reales. No se deben registrar cifras estimadas o inventadas.

## Procedimiento

1. Colocar al menos 15 fotografías reales en `services/stego/tools/calibracion/`.
2. Ejecutar:

```bash
PYTHONPATH=services/stego python services/stego/tools/stego_lab.py calibrate services/stego/tools/calibracion
```

3. Registrar la salida, los umbrales elegidos y el commit que los fija.
4. Repetir `pytest services/stego -q` después de cambiar los umbrales.

## Resultados

| Variante | Muestras | Detectadas | TPR/FPR | Umbral chi² | Umbral RS |
|---|---:|---:|---:|---:|---:|
| Limpias | 39 | 31 limpias, 8 revisión manual | FPR estadístico 20.51% | 0.995 | 0.15 |
| LSB secuencial 5 % | 39 | 27 limpias, 12 revisión manual | TPR 30.77% | 0.995 | 0.15 |
| LSB secuencial 10 % | 39 | 2 limpias, 37 revisión manual | TPR 94.87% | 0.995 | 0.15 |
| LSB secuencial 25 % | 39 | 39 revisión manual | TPR 100% | 0.995 | 0.15 |
| LSB aleatorio 5 % | 39 | 30 limpias, 9 revisión manual | TPR 23.08% | 0.995 | 0.15 |
| LSB aleatorio 10 % | 39 | 22 limpias, 17 revisión manual | TPR 43.59% | 0.995 | 0.15 |
| LSB aleatorio 25 % | 39 | 39 revisión manual | TPR 100% | 0.995 | 0.15 |
| LSB aleatorio 50 % | 39 | 39 revisión manual | TPR 100% | 0.995 | 0.15 |

> Estos valores corresponden a una muestra local de 39 imágenes. Las alertas estadísticas se clasifican como `revision_manual`; no prueban por sí solas la existencia de esteganografía. La detección estructural se verifica aparte con las imágenes de demo.

Los resultados solo se marcan como implementados después de ejecutar el procedimiento con las imágenes reales.
