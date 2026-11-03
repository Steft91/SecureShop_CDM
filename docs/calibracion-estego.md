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
| Limpias | 15 | Pendiente de confirmar | Pendiente | 0.995 | 0.15 |
| LSB secuencial 10 % | 15 | Pendiente de confirmar | Pendiente | 0.995 | 0.15 |
| LSB aleatorio 50 % | 15 | Pendiente de confirmar | Pendiente | 0.995 | 0.15 |

> Estos valores son una calibración inicial sobre la muestra local. Deben confirmarse ejecutando nuevamente el laboratorio después de cambiar los umbrales.

Los resultados solo se marcan como implementados después de ejecutar el procedimiento con las imágenes reales.
