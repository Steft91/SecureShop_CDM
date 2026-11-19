# Respuestas — Actividad Taller 02: Detección de vulnerabilidades OWASP Top 10 con minería de datos

**Notebook:** `notebook_modificado.ipynb` (notebook base + celdas de la actividad, ejecutado completo)
**Semilla:** `SEED = 42` en todos los experimentos

> Nota general: en el escenario base (`n_por_clase=80`) los tres modelos obtienen accuracy de 1.00 o muy cercano. Esto no significa que el clasificador sea perfecto: el dataset es sintético, se genera a partir de 10 plantillas por clase y el conjunto de prueba contiene casi los mismos fragmentos que el de entrenamiento. Esta observación aparece en varias respuestas porque explica la mayoría de resultados.

---

## Parte A — Exploración del dataset

### Respuesta A.1

| Categoría | Fragmentos |
|---|---:|
| A01_Broken_Access_Control | 80 |
| A02_Cryptographic_Failures | 80 |
| A03_Injection | 80 |
| A04_Insecure_Design | 80 |
| A05_Security_Misconfiguration | 80 |
| A06_Vulnerable_Components | 80 |
| A07_Auth_Failures | 80 |
| A08_Integrity_Failures | 80 |
| A09_Logging_Failures | 80 |
| A10_SSRF | 80 |
| **Total** | **800** |

El dataset está **perfectamente balanceado**: las 10 clases tienen 80 muestras, así que la diferencia entre la clase mayor y la menor es 0 % (muy por debajo del umbral de 10 %). El balance no es casual: `generar_dataset` crea exactamente `n_por_clase` fragmentos por categoría. Con `test_size=0.25` y `stratify=y`, quedan 600 fragmentos de entrenamiento y 200 de prueba (20 por clase). Por eso el accuracy es una métrica representativa aquí y no hace falta ponderar las clases.

### Respuesta A.2

| n_por_clase | Fragmentos de prueba | Accuracy Random Forest |
|---|---:|---:|
| 80 | 200 | 1.0000 |
| 30 | 75 | 0.8800 |

El accuracy **bajó 12 puntos porcentuales** (de 1.00 a 0.88), dentro del rango esperado de 5 a 15 puntos.

Recall por categoría con `n_por_clase=30`:

| Categoría | Recall (80) | Recall (30) | Caída |
|---|---:|---:|---:|
| **A06_Vulnerable_Components** | 1.000 | **0.714** | **0.286** |
| A03_Injection | 1.000 | 0.750 | 0.250 |
| A05_Security_Misconfiguration | 1.000 | 0.750 | 0.250 |
| A02_Cryptographic_Failures | 1.000 | 0.857 | 0.143 |
| A04_Insecure_Design | 1.000 | 0.875 | 0.125 |
| A07_Auth_Failures | 1.000 | 0.875 | 0.125 |
| A01, A08, A09, A10 | 1.000 | 1.000 | 0.000 |

Confusiones de la matriz con `n_por_clase=30` (real → predicho): A03 → A10 (2), A05 → A09 (2), A06 → A07 (2), A02 → A05 (1), A04 → A07 (1) y A07 → A02 (1).

La categoría más afectada fue **A06_Vulnerable_Components**: 2 de sus 7 fragmentos de prueba se clasificaron como A07. Las plantillas de A06 son casi solo nombres de librerías y números de versión (`log4j-core 2.14.1`, `openssl 1.0.1f`, `FROM node:8`). Cada plantilla es muy distinta de las demás y no comparte un vocabulario común como "md5" o "pickle". Con 30 muestras por clase, cada una de las 10 plantillas aparece unas 3 veces, así que algunas pueden caer solo en el conjunto de prueba. Cuando eso pasa, el modelo no tiene nada que memorizar y adivina a partir de tokens genéricos. El enunciado anticipaba A04 o A09; en este experimento A09 no se vio afectada y A04 solo perdió un fragmento.

Al terminar se restauró el escenario de `n_por_clase=80`. En el notebook el experimento usa un `df30` separado, así que el `df` original nunca se modificó.

---

## Parte B — Preprocesamiento y vectorización

### Respuesta B.1

`tokenizer_codigo("cursor.execute(f'SELECT * FROM users WHERE id={user_id}')")` genera **11 tokens**:

```
['cursor', 'execute', 'f', 'select', '*', 'from', 'users', 'where', 'id', '=', 'user_id']
```

**Por qué separa símbolos e identificadores.** La expresión regular `[a-z_][a-z0-9_]*|[0-9]+|[=<>!+\-*/%&|^]+` separa los identificadores de los operadores. Así un mismo identificador (`id`, `user_id`) se reconoce en cualquier contexto y no queda pegado a la puntuación que lo rodea. Los operadores se guardan como tokens propios porque tienen significado para la seguridad: `+` indica concatenación de cadenas (típica de SQLi y command injection), `=` indica asignación o comparación y `*` aparece en `SELECT *`. Un detalle importante: `(`, `)`, `.`, `'`, `{` y `}` **no** están en la expresión regular, así que el tokenizador los descarta y solo actúan como separadores. Por eso `cursor.execute(` queda en `cursor` y `execute`.

**Con `texto.split()`** salen solo **6 tokens**, y varios son inútiles:

```
["cursor.execute(f'SELECT", '*', 'FROM', 'users', 'WHERE', "id={user_id}')"]
```

Tokens como `cursor.execute(f'SELECT` o `id={user_id}')` mezclan varias palabras con puntuación y casi nunca se repiten en otro fragmento. Además distingue mayúsculas (`SELECT` ≠ `select`). Probado en el notebook con bigramas, el vocabulario baja a 1245 términos (frente a 1567), y aun así el Random Forest mantiene accuracy 1.00. Esto no demuestra que `split()` sea bueno: el conjunto de prueba repite casi literalmente las plantillas de entrenamiento, así que hasta los tokens "basura" coinciden. Con código real, escrito por personas distintas, `split()` generalizaría mucho peor.

### Respuesta B.2

| ngram_range | Tamaño del vocabulario | Accuracy RF | Tiempo (s) |
|---|---:|---:|---:|
| (1, 1) | 565 | 1.0000 | 1.06 |
| (1, 2) | 1567 | 1.0000 | 1.03 |
| (1, 3) | 2595 | 1.0000 | 1.05 |

El accuracy es igual en las tres configuraciones, pero el vocabulario crece mucho: los bigramas multiplican por 2.8 el número de variables y los trigramas por 4.6. Con 800 fragmentos el tiempo no cambia (alrededor de 1 s, porque domina el costo fijo del bosque), pero con datasets grandes la memoria y el tiempo crecen con el vocabulario.

**Con este dataset la mejor configuración es (1, 1).** Logra el mismo accuracy con la cuarta parte de las variables: es más barato, menos propenso al sobreajuste y más fácil de interpretar en SHAP. Para un dataset real recomendaría **(1, 2)** como término medio. Los bigramas capturan contexto que un unigrama pierde (`shell =`, `md5 encode`, `request get`), y ese contexto ayuda a distinguir, por ejemplo, `subprocess.run([...])` seguro de `subprocess.call(..., shell=True)`. (1, 3) no se justifica: casi duplica el vocabulario respecto a (1, 2) y no aporta nada.

---

## Parte C — Modelado

### Respuesta C.1

| n_estimators | Accuracy RF | Tiempo de entrenamiento (s) |
|---:|---:|---:|
| 10 | 1.0000 | 0.11 |
| 100 | 1.0000 | 0.39 |
| 300 | 1.0000 | 1.04 |

**No, el accuracy no mejora indefinidamente.** Agregar árboles reduce la varianza del bosque, pero esa ganancia es cada vez menor: con pocos árboles el promedio ya es estable y los nuevos árboles casi no cambian el voto mayoritario. El costo, en cambio, crece de forma lineal: 300 árboles tardan unas 10 veces más que 10.

En este experimento el accuracy ya está saturado en 1.00 con **10 árboles**, así que todo árbol adicional es costo sin beneficio. Pasa porque la tarea es casi trivial para el modelo, ya que el test repite plantillas del entrenamiento. En un problema real la curva suele estabilizarse entre 100 y 200 árboles. Ese rango es donde deja de ser rentable seguir agregando árboles, y conviene confirmarlo con validación cruzada en lugar de un único split.

### Respuesta C.2

| Modelo | Accuracy | F1 macro | Errores en 200 fragmentos |
|---|---:|---:|---:|
| Regresión Logística | 1.0000 | 1.00 | 0 |
| Random Forest (300 árboles) | 1.0000 | 1.00 | 0 |
| **Multinomial Naive Bayes** | **0.9950** | 0.99 | **1** |

Naive Bayes queda muy cerca de los otros dos: comete **un solo error**. Su precision en A03_Injection es 0.95 (20 / 21) y su recall en A10_SSRF es 0.95 (19 / 20), así que el error es **un fragmento de A10_SSRF clasificado como A03_Injection**.

- **Dónde funciona mejor:** en ocho categorías (A01, A02 y A04–A09) obtiene F1 = 1.00, igual que los otros modelos. Le va especialmente bien donde hay palabras muy distintivas que no aparecen en otras clases (`md5`, `des`, `pickle`, `yaml`, `debug`).
- **Dónde funciona peor:** en **A10_SSRF** (F1 = 0.974) y **A03_Injection** (F1 = 0.976). Las dos categorías comparten vocabulario: entrada del usuario (`request`, `get`, `user_input`) que llega a una función peligrosa. Naive Bayes asume que las palabras son independientes, así que no distingue si `request.get(...)` termina en `eval(...)` (A03) o en `requests.get(url)` (A10).

**Interpretación:** con 200 fragmentos de prueba, un error equivale a 0.5 puntos, así que no hay diferencias estadísticamente relevantes entre los tres modelos. Aun así, Naive Bayes tiene ventajas prácticas: entrena en milisegundos, no necesita ajustar hiperparámetros y es una buena línea base para texto. Regresión Logística ofrece pesos interpretables por token. Random Forest es el más costoso y, aquí, no aporta precisión adicional.

---

## Parte D — Interpretación de la matriz de confusión

**1. Par confundido sistemáticamente.** Con `n_por_clase=80`, la matriz del Random Forest es **diagonal**: 20 aciertos en cada clase y ninguna confusión. Para encontrar pares problemáticos usé la matriz del experimento A.2 (`n_por_clase=30`), donde el par más claro es **A03_Injection → A10_SSRF** (2 casos). Es el mismo par que confunde Naive Bayes (A10 → A03).

*Hipótesis:* las dos categorías tienen la misma estructura, "un dato del usuario llega sin validar a una función sensible". Comparten tokens: `request`, `get`, `url`, `user`, y en las plantillas de A03 aparece `eval(request.GET.get('expr'))` mientras A10 usa `request.GET.get('url')`. Un modelo basado en bolsa de palabras ve casi el mismo vocabulario y solo cambia el sumidero (`eval`/`execute` frente a `requests.get`/`urlopen`). Los otros pares de A.2 tienen explicaciones parecidas: A05 → A09 (configuraciones que mencionan `debug`/`logging`) y A06 → A07 (fragmentos sin vocabulario distintivo).

**2. Celda alta fuera de la diagonal.** Si `cm[i, j]` (fila real *i*, columna predicha *j*, con *i* ≠ *j*) tiene un valor alto, el modelo **confunde sistemáticamente la clase i con la clase j**. Cada uno de esos casos es un falso negativo para la clase *i*, que baja su recall, y un falso positivo para la clase *j*, que baja su precision. Suele indicar que las dos clases comparten vocabulario o que faltan ejemplos que las distingan.

**3. Precision manual de A03_Injection (Random Forest):**

$$\text{precision}_{A03} = \frac{TP}{TP + FP} = \frac{cm[A03, A03]}{\sum cm[:, A03]} = \frac{20}{20} = 1.00$$

El `classification_report` del Random Forest da **precision = 1.00** para A03_Injection, así que **coincide**. Como comprobación adicional con un caso no trivial, en Naive Bayes la columna de A03 suma 21 (20 aciertos y 1 fragmento de A10 mal clasificado): 20 / 21 = **0.952**, que coincide con el 0.95 de su reporte.

---

## Parte E — Explicabilidad SHAP y LIME

### Respuesta E.1

Top 5 tokens del gráfico SHAP global (importancia media |SHAP| sobre las 10 clases):

| # | Token | Importancia media |SHAP| |
|---|---|---:|
| 1 | `sin` | 0.0126 |
| 2 | `ssrf` | 0.0096 |
| 3 | `def` | 0.0065 |
| 4 | `/` | 0.0060 |
| 5 | `se` | 0.0056 |

**¿Se asocian a una categoría OWASP?** Solo `ssrf` se asocia directamente a una categoría (A10). Pero no viene del código: viene de los **comentarios** de las plantillas (`# SSRF clásico`, `// SSRF PHP`, `// SSRF Node.js`). Es decir, la etiqueta está escrita dentro del propio fragmento y el modelo la "lee". `def` es típico de los fragmentos en Python (A04, A07 y A01 tienen muchas funciones `def`), y `/` aparece en rutas y URLs (A01 path traversal, A10) y en los comentarios `//` de JavaScript, PHP y Java.

**¿Hay tokens que parezcan artefactos?** Sí, y son mayoría. `sin` y `se` son **palabras en español de los comentarios** que escribió el autor del dataset: "sin verificar rol", "sin auth", "sin hash", "sin SRI", "sin allowlist", "se permite acceso", "se traga la excepción". Ninguna es un rasgo de código vulnerable. Ningún token "de libro" como `md5` → A02 o `pickle` → A08 aparece en el top 5. El modelo se apoya mucho en los comentarios y en rasgos superficiales del lenguaje; si se quitaran los comentarios del preprocesamiento, el accuracy probablemente bajaría bastante.

### Respuesta E.2

| Fragmento | Categoría predicha | Confianza | ¿Es correcta? | Palabra más influyente en LIME |
|---|---|---:|---|---|
| 1 — SQLi por concatenación | A03_Injection | 64.44 % | **Sí** | `SELECT` (+0.120) |
| 2 — JWT con clave `'secret'` | A02_Cryptographic_Failures | 54.79 % | **Parcialmente**: la categoría es aceptable, pero por una razón débil | `key` (+0.247) |
| 3 — bcrypt bien usado | A04_Insecure_Design | 27.28 % | **No**: el código es seguro | `def` (+0.269) |

Segunda categoría más probable en cada caso: (1) A01 con 16.4 %, (2) A03 con 10.9 %, (3) A02 con 21.3 % y A07 con 21.0 %.

- **Fragmento 1.** LIME empuja hacia A03 con `SELECT` (+0.120), `FROM` (+0.057), `WHERE` (+0.025), `username` y `execute`. En contra empujan `def` (−0.139), `return`, `password`, `db` y `login`, palabras más típicas de A07 (autenticación). La explicación coincide con el riesgo real porque es una consulta SQL. Sin embargo, el modelo no "ve" la concatenación con `+`, que es lo que realmente hace vulnerable al código: LIME divide por palabras y los mismos tokens `SELECT FROM WHERE` aparecerían en una consulta parametrizada segura.
- **Fragmento 2.** Casi toda la predicción depende de `key` (+0.247), que en el entrenamiento aparece en plantillas A02 como `key = b'1234...'` y `DES.new(key, ...)`. El problema real es la **clave débil hardcodeada** `'secret'`, y LIME le da a `secret` un peso de casi cero (−0.0003); `jwt` y `HS256` tampoco influyen. La categoría A02 es defendible, porque un secreto hardcodeado es un fallo criptográfico (también podría ser A07), pero el modelo acertó por una coincidencia de vocabulario y no porque entendiera el riesgo.
- **Fragmento 3.** Es código seguro (bcrypt con `gensalt()`), pero el modelo no tiene clase "seguro" y está obligado a elegir una de las 10 categorías. Lo manda a A04 por el token `def` (+0.269), que no tiene relación con la seguridad. `bcrypt`, `hashpw` y `gensalt` pesan casi cero (alrededor de 0.001) porque **no existen en el vocabulario de entrenamiento**.

**Reflexión.** Confío más en el **fragmento 1**. Tiene la confianza más alta (64.4 %) y, sobre todo, una distancia clara con la segunda opción (16.4 %, casi cuatro veces menos). Además los tokens que LIME señala (`SELECT`, `FROM`, `WHERE`, `execute`) corresponden de verdad a la superficie de ataque de una inyección SQL. En el fragmento 2 la confianza ya es baja (54.8 %), y el 3 es claramente una predicción en la que no se puede confiar: las probabilidades están casi repartidas entre tres clases (27.3 %, 21.3 % y 21.0 %), lo que indica que el modelo no reconoce el patrón.

Lo que LIME aporta, y la probabilidad sola no, es el **porqué**. Con solo los números, el fragmento 2 parecería un acierto razonable. LIME revela que el modelo se fijó en `key` e ignoró `secret`, el verdadero problema, y que en el fragmento 3 la decisión la tomó un token irrelevante como `def`. LIME también deja ver una limitación de fondo: incluso en el caso correcto, la evidencia son palabras clave de SQL y no la concatenación insegura, así que el modelo marcaría igual una consulta parametrizada. Gracias a esto se puede saber cuándo una predicción "correcta" lo es por las razones equivocadas, y qué partes del código debe revisar una persona.

---

## Pregunta integradora final

No desplegaría el clasificador tal como está por estas tres razones:

1. **Su rendimiento es engañoso: aprende del dataset sintético y no de las vulnerabilidades.** El accuracy de 1.00 se debe a que test y entrenamiento comparten las mismas 10 plantillas por clase. Además, los tokens más influyentes según SHAP (`sin`, `ssrf`, `se`) salen de los comentarios en español, que en algunos casos contienen literalmente la etiqueta. Con el código de los estudiantes, sin esos comentarios y con estilos distintos, el rendimiento real es desconocido.
   *Mejora:* entrenar con código real etiquetado (CVEfixes, Juliet/SARD, OWASP Benchmark, o tareas pasadas revisadas por docentes), eliminar comentarios y literales en el preprocesamiento, y evaluar con un split por plantilla o por proyecto (`GroupKFold`) para medir la generalización real.

2. **No tiene clase "seguro", así que todo envío genera un falso positivo.** El modelo siempre asigna una de las 10 categorías: el código correcto con bcrypt se etiquetó como A04 *Insecure Design*. En un pipeline de corrección, cada tarea bien hecha recibiría una alerta, lo que generaría desconfianza y reclamos.
   *Mejora:* un esquema en dos etapas. Primero un detector binario vulnerable/seguro entrenado con ejemplos seguros reales; después el clasificador OWASP, solo para lo marcado como vulnerable. A eso se suma un umbral de confianza: por debajo de, por ejemplo, 70 %, el resultado se envía a revisión humana en lugar de reportarse.

3. **No entiende el flujo de datos y es fácil de evadir.** Un modelo de bolsa de palabras no distingue `"... WHERE id=" + uid` de `execute("... WHERE id=?", (uid,))`, porque los dos contienen `SELECT`, `WHERE` y `execute`. Basta con renombrar variables o quitar comentarios para cambiar la predicción, y además solo conoce los lenguajes y librerías de las plantillas (`bcrypt` no estaba en su vocabulario).
   *Mejora:* usarlo solo como **priorizador**, combinado con análisis estático que sí sigue el flujo de datos (Bandit, Semgrep o SonarQube). A mediano plazo, conviene probar representaciones de código como tokens de AST o embeddings tipo CodeBERT. La calificación final siempre debe quedar en manos del docente, usando las explicaciones LIME/SHAP como apoyo.
