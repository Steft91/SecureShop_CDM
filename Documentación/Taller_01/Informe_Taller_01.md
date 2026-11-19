# Informe — Actividad de reto: detector explicable de código vulnerable

**Notebook de soporte:** `Taller_01_Actividad_Reto.ipynb` (copia del notebook base con la sección *Actividad de reto* añadida y ejecutada).
**Dataset:** `code_vulnerabilities.csv` (Kaggle `ziya07/code-vulnerabilities-dataset`) + ejemplos sintéticos del notebook.

---

## 1. Fragmentos seleccionados y etiquetado manual

Se escribieron 10 fragmentos nuevos en 4 lenguajes. Ninguno aparece en el dataset de entrenamiento. Los 5 seguros son la versión corregida de los 5 vulnerables, para comprobar si el modelo distingue el patrón inseguro del seguro y no solo el tema.

| N.º | Tipo | Lenguaje | Código | Etiqueta | Justificación |
|---:|---|---|---|---|---|
| 1 | SQL Injection | Python | ``cursor.execute(f"SELECT * FROM orders WHERE customer_id = {request.args['id']}")`` | vulnerable | La entrada se interpola en el SQL; `1 OR 1=1` altera la consulta. |
| 2 | XSS | JavaScript | ``commentBox.innerHTML = '<p>' + params.get('comment') + '</p>';`` | vulnerable | Inserta entrada del usuario como HTML sin escapar. |
| 3 | Command Injection | PHP | ``$out = shell_exec("ping -c 4 " . $_GET['host']);`` | vulnerable | `host=8.8.8.8;rm -rf /` ejecuta comandos arbitrarios. |
| 4 | Path Traversal | Java | ``File report = new File("/srv/reports/" + request.getParameter("name")); …`` | vulnerable | `name=../../etc/passwd` lee archivos fuera del directorio. |
| 5 | Deserialización insegura | Python | ``session = pickle.loads(base64.b64decode(request.cookies.get('session')))`` | vulnerable | `pickle` ejecuta código al deserializar: RCE con una cookie manipulada. |
| 6 | Consulta parametrizada | Java | ``PreparedStatement ps = conn.prepareStatement("… WHERE customer_id = ?"); ps.setInt(1, customerId);`` | seguro | Parámetro enlazado; la entrada nunca se interpreta como SQL. |
| 7 | Salida con textContent | JavaScript | ``commentBox.textContent = params.get('comment');`` | seguro | `textContent` no interpreta HTML. |
| 8 | Comando sin shell | Python | ``subprocess.run(["ping", "-c", "4", host], shell=False, check=True, timeout=10)`` | seguro | Argumentos como lista y sin shell; `;` y `\|` no se interpretan. |
| 9 | Ruta validada | Python | ``full = os.path.realpath(os.path.join(BASE_DIR, name)); if not full.startswith(BASE_DIR + os.sep): abort(403)`` | seguro | Normaliza la ruta y verifica que quede dentro del directorio base. |
| 10 | Deserialización con JSON | Python | ``payload = json.loads(request.get_data(as_text=True))`` | seguro | JSON solo produce datos; no puede ejecutar código. |

## 2. Evaluación con el modelo del notebook

### 2.1 Modelo original (TF-IDF de palabras + Regresión Logística)

| N.º | Tipo de fragmento | Etiqueta real | Predicción | Prob. seguro | Prob. vulnerable | ¿Correcto? |
|---:|---|---|---|---:|---:|---|
| 1 | SQL Injection | vulnerable | seguro | 0.8016 | 0.1984 | **No** |
| 2 | XSS | vulnerable | vulnerable | 0.2418 | 0.7582 | Sí |
| 3 | Command Injection | vulnerable | vulnerable | 0.1901 | 0.8099 | Sí |
| 4 | Path Traversal | vulnerable | seguro | 0.8617 | 0.1383 | **No** |
| 5 | Deserialización insegura | vulnerable | seguro | 0.9024 | 0.0976 | **No** |
| 6 | Consulta parametrizada | seguro | seguro | 0.9455 | 0.0545 | Sí |
| 7 | Salida con textContent | seguro | seguro | 0.8753 | 0.1247 | Sí |
| 8 | Comando sin shell | seguro | seguro | 0.8743 | 0.1257 | Sí |
| 9 | Ruta validada | seguro | seguro | 0.9840 | 0.0160 | Sí |
| 10 | Deserialización con JSON | seguro | seguro | 0.9791 | 0.0209 | Sí |

**Aciertos: 7/10 (70 %).** Recall de `vulnerable` = 0.40; precision de `vulnerable` = 1.00.

Aunque en el notebook este modelo obtiene **accuracy = 1.0** en su conjunto de prueba, con código nuevo detecta solo 2 de 5 vulnerabilidades.

### 2.2 Modelo mejorado (ver sección 5)

| N.º | Tipo de fragmento | Etiqueta real | Predicción | Prob. seguro | Prob. vulnerable | ¿Correcto? |
|---:|---|---|---|---:|---:|---|
| 1 | SQL Injection | vulnerable | vulnerable | 0.2627 | 0.7373 | Sí |
| 2 | XSS | vulnerable | vulnerable | 0.1614 | 0.8386 | Sí |
| 3 | Command Injection | vulnerable | vulnerable | 0.3693 | 0.6307 | Sí |
| 4 | Path Traversal | vulnerable | vulnerable | 0.2780 | 0.7220 | Sí |
| 5 | Deserialización insegura | vulnerable | vulnerable | 0.1959 | 0.8041 | Sí |
| 6 | Consulta parametrizada | seguro | seguro | 0.6151 | 0.3849 | Sí |
| 7 | Salida con textContent | seguro | seguro | 0.6810 | 0.3190 | Sí |
| 8 | Comando sin shell | seguro | seguro | 0.5523 | 0.4477 | Sí |
| 9 | Ruta validada | seguro | seguro | 0.8515 | 0.1485 | Sí |
| 10 | Deserialización con JSON | seguro | vulnerable | 0.2580 | 0.7420 | **No** |

**Aciertos: 9/10 (90 %).** Recall de `vulnerable` = 1.00; precision de `vulnerable` = 0.83.

## 3. Explicabilidad con LIME

Se explicaron 3 fragmentos vulnerables que el modelo mejorado clasificó como `vulnerable`. El modelo original solo predijo `vulnerable` en dos casos, así que no alcanzaba para tres. LIME se configuró con `random_state=42` y 3000 muestras, y los tokens se separan también por símbolos de código. Un peso positivo empuja hacia `vulnerable`.

### 3.1 Fragmento 1 — SQL Injection (P(vulnerable) = 0.74)

| Token | Peso |
|---|---:|
| `cursor` | −0.143 |
| `request` | **+0.127** |
| `execute` | −0.075 |
| `args` | **+0.067** |
| `SELECT` | +0.038 |
| `customer_id` | +0.037 |
| `f` | +0.022 |
| `WHERE` | +0.020 |

- **Tokens hacia `vulnerable`:** `request` y `args`, que indican entrada del usuario, más `SELECT`/`WHERE` y el prefijo `f` del f-string.
- **¿Coincide con el riesgo real?** En parte. El riesgo está en que `request.args` llega dentro del SQL a través del f-string, y LIME sí marca esos dos elementos (fuente y `f`). Pero `cursor` y `execute`, que son el sumidero, *restan*, porque en el entrenamiento aparecen sobre todo en las consultas parametrizadas seguras.
- **¿Vulnerabilidad real o palabras sospechosas?** Más bien palabras sospechosas. El modelo no ve la relación entre `{request.args['id']}` y la consulta: reaccionó a `request`.
- **Revisión manual:** la interpolación `{...}` dentro de la cadena SQL y el origen de `request.args['id']`.

### 3.2 Fragmento 3 — Command Injection en PHP (P(vulnerable) = 0.63)

| Token | Peso |
|---|---:|
| `shell_exec` | **+0.070** |
| `$_GET` | **+0.020** |
| `$out` | +0.014 |
| `host` | +0.006 |
| `ping` | −0.003 |

- **Tokens hacia `vulnerable`:** `shell_exec`, que es el sumidero, y `$_GET`, que es la fuente.
- **¿Coincide con el riesgo real?** Sí. Es la explicación técnicamente más razonable de las tres: señala la función peligrosa y la entrada no confiable. `$out` aporta un peso pequeño y espurio.
- **¿Vulnerabilidad real o palabras sospechosas?** Detecta los ingredientes correctos, pero no la concatenación `.` que los une. Probablemente daría una predicción parecida si `$_GET['host']` estuviera protegido con `escapeshellarg()`, porque ese caso seguro nunca se vio en el entrenamiento. Además la confianza es baja (0.63): ni `shell_exec` ni PHP aparecen en el entrenamiento, así que la señal viene de coincidencias parciales de caracteres con ejemplos como `shell=True`.
- **Revisión manual:** la concatenación `"ping -c 4 " . $_GET['host']` y la ausencia de `escapeshellarg`/validación de IP.

### 3.3 Fragmento 5 — Deserialización insegura (P(vulnerable) = 0.80)

| Token | Peso |
|---|---:|
| `request` | **+0.141** |
| `get` | **+0.084** |
| `loads` | **+0.069** |
| `session` | −0.063 |
| `pickle` | **+0.059** |
| `b64decode` | −0.011 |
| `base64` | −0.010 |
| `cookies` | +0.007 |

- **Tokens hacia `vulnerable`:** `request`, `get`, `loads` y `pickle`.
- **¿Coincide con el riesgo real?** En parte. `pickle` + `loads` sobre datos de `request.cookies` es exactamente el riesgo, pero `request` pesa más que `pickle`, cuando el peligro real es `pickle`. `cookies`, que es la fuente concreta, apenas cuenta.
- **¿Vulnerabilidad real o palabras sospechosas?** El falso positivo del fragmento 10 lo confirma: el modelo depende de `request` y `loads` más que de `pickle`.
- **Revisión manual:** el uso de `pickle.loads` sobre cualquier dato externo. Debería sustituirse por JSON o por datos firmados (HMAC).

### 3.4 LIME complementario (casos de error)

- **Falso positivo del modelo mejorado (fragmento 10, `json.loads(request…)`):** `request` (+0.234) y `loads` (+0.110) dominan, y `json` casi no cuenta (−0.006). El modelo aprendió “`request` + `loads` ⇒ vulnerable” a partir de la plantilla `pickle.loads(request.data)`.
- **Falso negativo del modelo original (fragmento 1):** todos los tokens con peso relevante empujan hacia `seguro` (`id` −0.160, `cursor` −0.101, `SELECT` −0.095, `FROM` −0.094). Ese modelo asocia el vocabulario SQL con la clase segura (ver sección 4).

## 4. Análisis de errores

| Modelo | Falsos positivos | Falsos negativos |
|---|---|---|
| Original | 0 | 3 (n.º 1 SQLi, n.º 4 Path Traversal, n.º 5 pickle) |
| Mejorado | 1 (n.º 10 `json.loads`) | 0 |

**Causas de los falsos negativos del modelo original.** Se identificaron revisando el notebook (celda *Diagnóstico*):

1. **Se entrenó con la columna equivocada.** La heurística `guess_code_column` eligió `Preprocessed Tokens`, que contiene texto como `["cursor.execute('SELECT", '*', 'FROM', …]`, en lugar de `Code Snippet`. Los ejemplos vulnerables tienen formato de lista de Python y los seguros formato de código: el modelo aprende a distinguir **formatos**, no vulnerabilidades.
2. **Fuga de información.** Cada ejemplo seguro termina en `# safe_example_N`. Ese token solo existe en una clase, y eso explica el accuracy de 1.0 en el conjunto de prueba, que es engañoso.
3. **Poca variedad.** El CSV tiene 1000 filas pero solo **10 fragmentos únicos**, y solo de SQLi y XSS. Path Traversal y deserialización nunca se vieron, de ahí los FN n.º 4 y 5.
4. **Patrones superficiales e invertidos.** Los seguros sintéticos contienen `cursor.execute('SELECT … ?')` en texto plano, de modo que `cursor`, `SELECT` y `FROM` empujan hacia `seguro`. Una SQLi escrita con f-string (n.º 1) cae del lado seguro.

**Causa del falso positivo del modelo mejorado.** La vulnerabilidad depende del contexto y no solo del texto: `json.loads` y `pickle.loads` comparten casi todos los tokens (`loads`, `request`, `get`), y lo único que los diferencia es el nombre del módulo. Con solo un ejemplo de cada tipo, el modelo no puede aprender esa diferencia.

## 5. Propuesta de mejora (implementada)

| # | Cambio | Motivo |
|---|---|---|
| 1 | Usar `Code Snippet` (código real) en vez de `Preprocessed Tokens` | Eliminar el sesgo de formato entre clases. |
| 2 | Eliminar el comentario `# safe_example_N` / `# vulnerable_example_N` | Quitar la fuga de información. |
| 3 | Deduplicar ejemplos | Evitar que el mismo fragmento esté en train y test. |
| 4 | Agregar las plantillas vulnerables del notebook (command injection, path traversal, pickle, eval, md5, control de acceso) | Cubrir más tipos de vulnerabilidad, no solo SQLi/XSS. |
| 5 | Combinar TF-IDF de palabras (1–2 gramas) con TF-IDF de **caracteres** (`char_wb`, 2–5 gramas) | Generalizar entre lenguajes y variantes (`shell_exec` ≈ `shell=True`, `$_GET` ≈ `get`). |
| 6 | Regresión Logística con `C=10` y `class_weight="balanced"` | Con solo 30 ejemplos únicos, la regularización por defecto deja todas las probabilidades cerca de 0.5. |

**Resultado:** el recall de `vulnerable` pasa de 0.40 a 1.00 en los fragmentos nuevos, y el accuracy de 70 % a 90 %.

**Advertencia honesta:** la validación cruzada del modelo mejorado sobre sus 30 ejemplos únicos da un **F1-macro ≈ 0.43 ± 0.10**. Esa cifra es baja, pero es una estimación más realista que el 1.0 del notebook original. El 9/10 sobre solo 10 fragmentos no es estadísticamente concluyente. La mejora corrige errores metodológicos, pero el cuello de botella sigue siendo el dataset.

**Mejoras siguientes recomendadas:**

- **Datos reales:** usar datasets con pares vulnerable/corregido (Big-Vul, CVEfixes, Juliet Test Suite) y separar train/test por proyecto para evitar fugas.
- **Representación semántica:** usar modelos de código preentrenados (CodeBERT, UniXcoder) o representaciones del AST y del flujo de datos, en lugar de bolsa de tokens.
- **Modelo híbrido:** combinar el clasificador con análisis estático (Semgrep, Bandit, CodeQL), que rastrea el flujo fuente→sumidero. El modelo serviría para priorizar y el analizador estático para confirmar.
- **Separar por tipo de vulnerabilidad (CWE)** para medir el desempeño por categoría.

## 6. Respuestas a las preguntas guía

- **¿Qué vulnerabilidad fue más fácil de detectar?** XSS con `innerHTML` y Command Injection: ambos modelos los detectaron. XSS tiene la mayor confianza (0.76 y 0.84) porque es uno de los dos tipos presentes en Kaggle.
- **¿Qué fragmentos confundieron al modelo?** La SQLi con f-string, Path Traversal y pickle confundieron al original. `json.loads(request…)` confundió al mejorado. La consulta parametrizada (0.38) y el comando sin shell (0.45) quedaron cerca del umbral.
- **¿Qué tokens llevaron a predecir `vulnerable`?** Fuentes de entrada (`request`, `args`, `$_GET`, `get`) y sumideros (`shell_exec`, `pickle`, `loads`, `innerHTML`).
- **¿Fueron razonables las explicaciones de LIME?** Parcialmente. Señalan fuentes y sumideros plausibles, pero también muestran que el modelo no ve la relación entre ambos y que da pesos negativos a tokens como `cursor`/`execute` por artefactos del dataset. LIME fue más útil para encontrar los defectos del modelo que para justificar sus aciertos.
- **¿Qué riesgos tiene usarlo sin revisión humana?** Los falsos negativos dan una falsa sensación de seguridad: el modelo original dejó pasar 3 de 5 vulnerabilidades, incluida una RCE con pickle. Los falsos positivos generan fatiga de alertas. Además, un atacante podría evadirlo renombrando variables (por ejemplo, evitando la palabra `request`).
- **¿Cómo mejorar el dataset?** Con código real, ambas clases provenientes de la misma fuente, pares vulnerable/corregido, más tipos de CWE y lenguajes, sin duplicados ni marcas que delaten la clase, y con separación train/test por proyecto.

## 7. Conclusión

El enfoque TF-IDF + clasificador + LIME es útil como herramienta **educativa y de priorización**. Es rápido, interpretable y, con datos limpios, reconoce fuentes y sumideros típicos. Sus limitaciones también quedaron claras:

1. Evalúa texto, no semántica. No sabe si la entrada está validada ni si `json` es distinto de `pickle`.
2. Su calidad depende por completo del dataset. El accuracy de 1.0 del notebook escondía un modelo que detectaba solo 40 % de las vulnerabilidades nuevas.
3. LIME sirve sobre todo para auditar el modelo: permitió descubrir el uso de la columna equivocada y los atajos aprendidos.

Un detector así no debe reemplazar la revisión humana, las pruebas de seguridad ni las herramientas de análisis estático y dinámico. Su lugar es como un filtro previo cuyos resultados siempre revisa una persona.
