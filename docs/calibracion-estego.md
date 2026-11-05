# Calibración y justificación del estegoanálisis

El servicio `stego` busca indicios de datos ocultos en imágenes PNG con tres estadísticos sobre el plano del bit menos significativo (LSB) y una revisión de la estructura del archivo. En JPEG, GIF y WAV solo revisa la estructura. El resultado es un indicio y no prueba que haya esteganografía.

## Técnica y parámetros

| Detector | Qué mide | Parámetro | Valor | Por qué |
|---|---|---|---|---|
| Chi² de pares de valores (Westfeld y Pfitzmann) | Al reemplazar LSB con bits aleatorios, cada par de valores (2k, 2k+1) tiende a igualar sus frecuencias. El detector calcula el p-valor de esa igualdad sobre el 10, 25, 50 y 100 % de los píxeles de cada canal y se queda con el mayor | `STEGO_CHI2_P` | 0,995 | Umbral alto para limitar falsos positivos: con él y el de RS, el FPR medido es 20,5 % (tabla de resultados) |
| Análisis RS (Fridrich, Goljan y Du) | Estima la fracción de píxeles con el LSB modificado comparando grupos "regulares" y "singulares" bajo las máscaras de volteo F₁ y F₋₁ | `STEGO_RS_RATE` | 0,15 | Fracción estimada a partir de la cual se alerta; con este valor, el LSB secuencial al 10 % se detecta en el 94,9 % de la muestra |
| Entropía del plano LSB | Entropía media del LSB en bloques de 64 × 64 y la fracción de bloques con entropía ≥ 0,999 | `STEGO_ENTROPY_TRIGGER` | desactivado | Se informa como indicador; no decide porque las zonas con ruido ya tienen entropía máxima |
| Estructura PNG | Bytes después de `IEND`, chunks de texto de más de 1024 bytes y chunks desconocidos | — | — | Es la forma más común de esconder un archivo entero (por ejemplo un ZIP) |
| Estructura JPEG, GIF y WAV | Bytes después de `EOI`, del trailer GIF o del RIFF declarado; metadatos y comentarios excesivos | — | — | Igual que en PNG, sin analizar píxeles ni muestras |

Una imagen con menos de 1000 píxeles no tiene muestra suficiente para chi² ni para RS: sus métricas salen como `null` y el resultado es `no_concluyente`. Si el análisis falla o pasa de `STEGO_TIMEOUT_S` (10 s), el resultado también es `no_concluyente`, nunca `sin_indicios`.

## Veredicto y política

| `status` | Cuándo | `action` |
|---|---|---|
| `sin_indicios` | Ningún detector supera su umbral | `ninguna`: el archivo se descarta |
| `sospechoso` | Una anomalía estructural o un estadístico sobre su umbral | `cuarentena`: el archivo queda en el volumen `stego_quarantine` con permisos `0600` |
| `no_concluyente` | Tiempo excedido, fallo del análisis o imagen demasiado pequeña | `advertencia` |
| `error` | Firma, extensión o `Content-Type` no admitidos (415), o archivo truncado o demasiado grande en píxeles (422) | `rechazo`: no se analiza |

## Procedimiento de calibración

1. Colocar al menos 15 fotografías reales en `services/stego/tools/calibracion/`; esa carpeta no se versiona.
2. Ejecutar desde la raíz:

```bash
python services/stego/tools/stego_lab.py calibrate services/stego/tools/calibracion
```

3. El laboratorio reduce cada foto a 1024 px como máximo, la guarda como PNG y la analiza limpia y con LSB embebido, secuencial y aleatorio, al 5, 10, 25 y 50 % de la capacidad.
4. Si se cambian los umbrales, se actualizan en `stego_svc/config.py`, en `services/stego/.env.example` y en la skill `stego-analysis`, y se vuelve a correr `pytest services/stego -q`.

## Resultados

Muestra local de 39 fotografías con los umbrales de la tabla (chi² 0,995, RS 0,15). "Detectadas" son las que el servicio clasifica como `sospechoso`.

| Variante | Muestras | `sin_indicios` | `sospechoso` | Tasa |
|---|---:|---:|---:|---:|
| Limpias | 39 | 31 | 8 | FPR 20,51 % |
| LSB secuencial 5 % | 39 | 27 | 12 | TPR 30,77 % |
| LSB secuencial 10 % | 39 | 2 | 37 | TPR 94,87 % |
| LSB secuencial 25 % | 39 | 0 | 39 | TPR 100 % |
| LSB aleatorio 5 % | 39 | 30 | 9 | TPR 23,08 % |
| LSB aleatorio 10 % | 39 | 22 | 17 | TPR 43,59 % |
| LSB aleatorio 25 % | 39 | 0 | 39 | TPR 100 % |
| LSB aleatorio 50 % | 39 | 0 | 39 | TPR 100 % |

## Imágenes de la demo

`python services/stego/tools/stego_lab.py demo docs/demo-imagenes` genera estas imágenes de forma determinista. Las prueba `services/stego/tests/test_demo.py` y las usa la colección de Postman.

| Archivo | Qué es | Resultado esperado |
|---|---|---|
| `referencia.png` | Imagen sintética de 256 × 256 sin modificar | `200`, `sin_indicios` (chi² p ≈ 0,38; RS ≈ 0,013) |
| `lsb.png` | La misma con LSB aleatorio al 50 % | `200`, `sospechoso` por RS |
| `zip-al-final.png` | La referencia con un ZIP pegado después de `IEND` | `200`, `sospechoso` por estructura |
| `no-es-imagen.png` | Bytes con cabecera `MZ` (ejecutable) renombrados a `.png` | `415` |
| `truncada.png` | La referencia cortada a la mitad | `422` |
| `grande.png` | Ruido de 1400 × 1400, unos 5,9 MB; no se versiona | `413` |

## Limitaciones

- El FPR de 20,5 % en limpias implica que una de cada cinco fotos naturales queda `sospechoso`. Por eso el resultado es un indicio y la política es cuarentena, no borrado.
- Con LSB al 5 % la detección es baja (23–31 %): un mensaje corto pasa desapercibido.
- LSB matching (±1) y el embebido adaptativo no producen el patrón de pares que mide chi², y pueden evadir chi² y RS.
- JPEG, GIF y WAV solo tienen análisis estructural: el embebido en los coeficientes DCT o en las muestras de audio no se detecta.
- La muestra de 39 fotos es pequeña y local; las tasas son orientativas.
- La cuarentena no tiene cuota ni retención automática; la limpieza es manual (`docker volume`).`r`n- No hay una revisión humana del veredicto: `sospechoso` es un indicio automatizado y se conserva en cuarentena para una futura revisión autorizada.
