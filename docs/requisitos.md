# Requisitos funcionales, no funcionales y de seguridad

| | |
|---|---|
| **Fuente oficial** | [Actividad 3 aprobada](../Documentación/Tarea%203/Díaz_Cedeño_Manangón_Actividad3.md): 21 RF, 19 RNF y 39 RS, con su criterio de aceptación, prioridad y la trazabilidad con los riesgos R1–R15 (Tabla 7). Ese documento manda en el texto y el criterio de cada requisito; aquí solo se resumen |
| **Además** | Lo que pidió el docente en la clase del 22/10/2026 para el primer parcial (RC- y RP-) |
| **Fecha** | 2026-10-26 |
| **Uso** | Los planes, los tickets y `docs/trazabilidad-riesgos.md` se refieren a estos IDs. La columna *Primer parcial* dice qué cubre la entrega actual (gateway, `auth` y `stego`) |

**Primer parcial:**
- **Sí:** el parcial lo cumple completo. *Plan* dice qué tarea lo construye y *Verificación*, qué test lo prueba.
- **Parcial:** el parcial cubre la parte indicada; el resto llega con las salas, el chat, los archivos o la auditoría.
- **No:** depende de piezas que todavía no se construyen. Queda para los parciales 2 y 3.

---

## 1. Requisitos del docente para el primer parcial (clase del 22/10)

| ID | Requisito | Plan | Verificación |
|---|---|---|---|
| RC-01 | El login entrega un **JWT** firmado (RS256) que solo `auth` emite; el gateway lo verifica con `auth` en cada petición junto con la sesión a la que apunta | ATH-1, ATH-2, GW-1 | `test_login_entrega_jwt_y_sesion`, `test_alg_none_y_hs256_con_la_clave_publica_se_rechazan`, `test_jwt_de_sesion_terminada_401` |
| RC-02 | **Roles y RBAC:** el admin crea roles con permisos de un catálogo fijo (`users:manage`, `roles:manage`, `stego:analyze`) y los asigna; la cuenta nace sin roles; un cambio vale en la siguiente petición; el sistema nunca se queda sin admin | ATH-1, ATH-4 | `test_crear_rol_con_permisos`, `test_r05_rol_asignado_vale_en_la_siguiente_peticion`, `test_r05_no_se_quita_el_ultimo_admin` |
| RC-03 | **API de esteganografía** que se usa con el token de `auth` y responde si la imagen es inválida, limpia, con problema o para revisión manual | STG-1…STG-4, GW-1 | `test_imagen_limpia`, `test_r06_archivo_pegado_al_final_es_problema`, `test_r06_imagen_con_lsb_es_revision_manual`, `test_r09_archivo_que_no_es_imagen_es_invalida` |
| RP-10 | **Informe:** descripción de la aplicación, cómo se construyó, tipo de API (REST), tecnologías, bibliotecas y herramientas, e integración con `auth` | PAR-2 | `docs/informe-parcial-1.md` |
| RP-11 | **Demostración en vivo** con Postman: la API de esteganografía funcionando con el token de `auth` | PAR-1, PAR-3 | `docs/postman/parcial-1.postman_collection.json` y `docs/demo-parcial-1.md` |

---

## 2. Requisitos funcionales (Tabla 1)

| ID | Requisito | Primer parcial | Plan | Verificación |
|---|---|---|---|---|
| RF-01 | Cierre de sesión del administrador | **Sí** | ATH-2 | `test_me_y_logout`, `test_jwt_de_sesion_terminada_401` |
| RF-02 | Crear una sala con identificador único | No | — | — |
| RF-03 | Clave de acceso propia por sala | No | — | — |
| RF-04 | Número máximo de participantes | No | — | — |
| RF-05 | Tipo de comunicación de la sala | No | — | — |
| RF-06 | Consultar salas | No | — | — |
| RF-07 | Modificar una sala | No | — | — |
| RF-08 | Cerrar una sala | No | — | — |
| RF-09 | Consultar los eventos de seguridad, filtrando por severidad | **Parcial:** los eventos salen como registros JSON con su nivel y se filtran con `docker compose logs`; la consulta desde el panel llega con la auditoría | FND-4, PAR-3 | `test_formato_json_de_los_registros` |
| RF-10 | Revisión de la cuarentena | No | — | — |
| RF-11 | Ingreso autenticado a salas | No (la cuenta autenticada ya existe: RF-20, RF-21) | — | — |
| RF-12 | Salida voluntaria de la sala | No | — | — |
| RF-13 | Cierre automático de sesiones inactivas o caídas | **Parcial:** la sesión de la cuenta vence por inactividad (30 min) y por tiempo absoluto (8 h); el cierre de conexiones del chat (15 min) llega con el chat | ATH-2 | `test_sesion_inactiva_libera_el_dispositivo`, `test_sesion_vencida_por_tiempo_absoluto_401` |
| RF-14 | Chat de texto en tiempo real | No | — | — |
| RF-15 | Avisos de entrada y salida, e historial | No | — | — |
| RF-16 | Respeto del tipo de sala | No | — | — |
| RF-17 | Subir documentos e imágenes | No (el parcial analiza PNG y JPEG sin publicarlos: RC-03) | — | — |
| RF-18 | Ver y descargar archivos autorizados | No | — | — |
| RF-19 | Formatos ampliables con análisis específico | **Parcial:** el punto de extensión `FORMATS` con PNG y JPEG; los demás formatos llegan con los archivos | STG-2 | `test_deteccion_por_firma_ignora_la_extension` |
| RF-20 | Registro obligatorio con identificador único, contraseña y alias visible | **Sí** | ATH-2 | `test_registro_crea_cuenta_sin_roles`, `test_usuario_duplicado_409`, `test_alias_duplicado_sin_distinguir_mayusculas_409`, `test_alias_invalido_422` |
| RF-21 | Inicio y cierre de sesión del participante | **Sí** (sin conexiones de chat que liberar todavía) | ATH-2 | `test_login_entrega_jwt_y_sesion`, `test_me_y_logout` |

---

## 3. Requisitos no funcionales (Tabla 2)

| ID | Atributo | Requisito | Primer parcial | Plan | Verificación |
|---|---|---|---|---|---|
| RNF-01 | Rendimiento | Latencia de entrega de mensajes | No | — | — |
| RNF-02 | Rendimiento | Tiempo de respuesta del ingreso a una sala | No | — | — |
| RNF-03 | Rendimiento | Tiempo de análisis de documentos e imágenes | **Parcial:** el análisis corre en otro proceso con tiempo máximo (`STEGO_TIMEOUT_S`); los objetivos por formato llegan con los archivos | STG-3 | `test_timeout_del_analisis_es_revision_manual` |
| RNF-04 | Disponibilidad | Disponibilidad mensual del servicio de chat | No | — | — |
| RNF-05 | Disponibilidad | Aislamiento de fallos del análisis multimedia | No | — | — |
| RNF-06 | Escalabilidad | Conexiones simultáneas | No | — | — |
| RNF-07 | Escalabilidad | Crecimiento del registro de auditoría | No | — | — |
| RNF-08 | Usabilidad | Primer ingreso sin ayuda | No (sin interfaz gráfica en el parcial) | — | — |
| RNF-09 | Usabilidad | Accesibilidad de la interfaz | No | — | — |
| RNF-10 | Mantenibilidad | Cobertura de pruebas ≥ 80 % por servicio | **Sí** | FND-7 | CI (`--cov-fail-under=80`) |
| RNF-11 | Mantenibilidad | Calidad estática: sin hallazgos altos o medios y complejidad ≤ 10 | **Sí** | FND-1, FND-7 | CI (`ruff` con `C90`, bandit, CodeQL) |
| RNF-12 | Mantenibilidad | Despliegue reproducible con un comando en ≤ 15 min | **Sí** | FND-6, PAR-3 | Ensayo de PAR-3 desde un clon limpio |
| RNF-13 | Interoperabilidad | Compatibilidad con navegadores | No | — | — |
| RNF-14 | Confiabilidad | Entrega completa y ordenada de mensajes | No | — | — |
| RNF-15 | Confiabilidad | Persistencia de las salas ante reinicios | No | — | — |
| RNF-16 | Recuperación | Respaldo y restauración | No | — | — |
| RNF-17 | Recuperación | Reinicio automático de servicios | **Parcial:** `restart: unless-stopped` y `healthcheck` en compose; la prueba de los 60 s llega después | FND-6 | `docker compose config` |
| RNF-18 | Monitoreo | Métricas y alertas de consumo | **Parcial:** comprobación de salud (`/health`) en cada servicio; métricas y alertas después | FND-4 | `test_health` (auth), `test_health_sin_bd` (stego) |
| RNF-19 | Monitoreo | Registros estructurados y trazables: fecha, servicio, nivel e id de correlación | **Sí** | FND-4, GW-1 | `test_formato_json_de_los_registros`, `test_el_id_del_gateway_llega_al_codigo_y_a_los_eventos`, `test_una_linea_por_peticion_sin_query_string`; curl de GW-1 |

---

## 4. Requisitos de seguridad (Tabla 3)

| ID | Requisito | Primer parcial | Plan | Verificación |
|---|---|---|---|---|
| RS-01 | Autenticación segura del administrador (segundo factor y bloqueo) | **Parcial:** contraseña Argon2id, bloqueo tras 5 fallos y retraso progresivo; el TOTP de los admins queda fuera del primer parcial y llega después | FND-3, ATH-2, ATH-3 | `test_r04_bloqueo_tras_5_fallos_por_usuario`, `test_el_admin_entra_con_su_contraseña` |
| RS-02 | Autorización del administrador en cada operación | **Sí** | FND-4, ATH-4 | `test_r05_sin_roles_manage_403`, `test_r05_sin_el_permiso_403_y_se_registra` |
| RS-03 | Clave de sala protegida | No | — | — |
| RS-04 | Ingreso controlado por intentos | No | — | — |
| RS-05 | Sesión ligada al dispositivo | **Sí** | ATH-2, GW-1 | `test_r13_jwt_con_otra_cookie_de_dispositivo_401` |
| RS-06 | Control de sesiones por cuenta | **Parcial:** una sola sesión viva por cuenta; el cupo de las salas llega con las salas | ATH-2 | `test_r13_login_desde_otro_dispositivo_409`, `test_r13_el_indice_unico_impide_dos_sesiones_vivas` |
| RS-07 | Cierre seguro de conexiones y cuentas | **Parcial:** cerrar sesión invalida el token; la salida de salas llega con las salas | ATH-2 | `test_me_y_logout`, `test_jwt_de_sesion_terminada_401` |
| RS-08 | Rechazo de credenciales mal usadas | **Parcial:** un token sin el permiso o desde otro dispositivo se rechaza; la cookie de sala llega con las salas | ATH-2, STG-3 | `test_r05_sin_el_permiso_403` (stego), `test_r13_jwt_con_otra_cookie_de_dispositivo_401` |
| RS-09 | Confidencialidad en tránsito | **Parcial:** TLS 1.3 entre el cliente y el gateway; el cifrado de cada mensaje llega con el chat | GW-1 | Verificación manual de GW-1 |
| RS-10 | Integridad de los mensajes | No | — | — |
| RS-11 | Autenticidad de las comunicaciones | No | — | — |
| RS-12 | Información protegida en reposo | No | — | — |
| RS-13 | Gestión de claves | **Parcial:** secretos solo en `/run/secrets`, el servicio no arranca sin ellos y los secretos se rotan con `gen_secrets.py --rotate`; la KEK llega con el cifrado en reposo | FND-2, FND-6 | `test_secreto_ausente_detiene_el_servicio`, `test_rotar_token_del_gateway_regenera_hash_y_conf` |
| RS-14 | Solo TLS 1.3 hacia el cliente | **Sí** | GW-1 | Verificación manual de GW-1: TLS 1.2 rechazado, http → 301 |
| RS-15 | Justificación criptográfica documentada | **Sí** (lo que existe en el parcial) | — | `docs/justificacion-criptografica.md` |
| RS-16 | Carga segura multiformato | **Parcial:** firma real, decodificación, topes de tamaño y de píxeles para PNG y JPEG | STG-2 | `test_r09_contenido_que_no_coincide_con_la_firma`, `test_r09_bomba_de_descompresion_rechazada`, `test_r09_archivo_demasiado_grande` |
| RS-17 | Descarga autorizada de documentos e imágenes | No | — | — |
| RS-18 | Detección de contenido oculto o sospechoso | **Parcial:** chi², RS y estructura en PNG y JPEG, con falsos positivos y negativos medidos | STG-1, STG-2, STG-4 | `test_r06_*`, tabla TPR/FPR en `docs/calibracion-estego.md` |
| RS-19 | Cuarentena y liberación controlada | No | — | — |
| RS-20 | Alerta oportuna de eventos de seguridad en el panel | No (los eventos `warning` quedan en los registros) | — | — |
| RS-21 | Bloqueo seguro ante fallas del análisis | No | — | — |
| RS-22 | Integridad verificable del registro de eventos | No | — | — |
| RS-23 | Protección de datos sensibles en registros | **Sí** | FND-4, todos | `test_una_linea_por_peticion_sin_query_string`; revisión con `security-auditor` |
| RS-24 | Registro obligatorio de operaciones críticas | No (necesita el servicio de auditoría) | — | — |
| RS-25 | Autenticación y autorización entre servicios | **Sí** | FND-4, ATH-2, STG-3 | `test_ruta_interna_respeta_la_allowlist`, `test_r16_verify_solo_para_el_gateway`, `test_r16_solo_acepta_el_token_del_gateway` |
| RS-26 | Mínimo privilegio de componentes | **Sí** | FND-6, ATH-1 | `test_r11_rol_app_confinado`, `test_r11_la_app_no_borra_cuentas_ni_edita_el_catalogo` |
| RS-27 | Rechazo de entradas no válidas | **Sí** | todos | `test_r05_cuerpo_con_campos_de_mas_422`, `test_politica_de_registro`, `test_alias_invalido_422`, bandit, CodeQL |
| RS-28 | Protección frente al abuso de recursos | **Sí** (en el gateway, `auth` y `stego`) | GW-1, ATH-2, STG-3 | `test_r10_tope_de_registros_por_ip`, `test_r10_limite_de_analisis_por_minuto` |
| RS-29 | Errores seguros sin filtración de información | **Sí** | FND-4 | `test_errores_genericos`, `test_error_generico_para_clave_mala_y_usuario_inexistente` |
| RS-30 | Revisión de riesgos desde el diseño | **Sí** | FND-1 | Spec §4 y §16, modelo de amenazas en `docs/cumplimiento-normativo.md` §5.3 |
| RS-31 | Verificación continua de identidad y permisos | **Sí** | FND-4, ATH-2, GW-1 | `test_identidad_solo_vale_si_la_trae_el_gateway`, `test_verify_devuelve_identidad_y_permisos_actuales` |
| RS-32 | Detección temprana de vulnerabilidades | **Sí** | FND-1, FND-7 | CI (ruff, bandit, pip-audit, CodeQL, gitleaks) |
| RS-33 | Asociación de riesgos con controles ISO/IEC 27001 | **Sí** | FND-1 | `docs/cumplimiento-normativo.md` §1 y la columna ISO de `docs/trazabilidad-riesgos.md` |
| RS-34 | Verificación documentada de controles de aplicación (ISO/IEC 27034) | **Sí** | FND-1 | `docs/cumplimiento-normativo.md` §2 |
| RS-35 | Respuestas de ingreso que no revelan el estado de la sala | No | — | — |
| RS-36 | Revisión de archivos después de su saneamiento | No | — | — |
| RS-37 | Revisión obligatoria de cambios de código | **Sí** | FND-1, FND-7 | Plantilla de PR y regla de `main` en GitHub |
| RS-38 | Registro y autenticación obligatorios de participantes | **Sí** | FND-3, ATH-2, GW-1 | `test_registro_crea_cuenta_sin_roles`, `test_hash_es_argon2id_con_parametros_rfc9106`, `test_r04_*` |
| RS-39 | Autorización por cuenta para salas y archivos | **Parcial:** el análisis exige una cuenta con sesión activa y el permiso; las salas y los archivos llegan después | STG-3, GW-1 | `test_sin_identidad_del_gateway_401`, `test_r05_sin_el_permiso_403` (stego) |

---

## 5. Decisiones de interpretación del primer parcial

1. **"Usuario" = cuenta registrada.** El registro es abierto y la cuenta nace sin permisos: los da el admin con un rol (RC-02).
2. **El alias (RF-20) es solo el nombre visible.** Es único sin distinguir mayúsculas, no autentica ni autoriza nada (RS-39) y no se transfiere. El alias del admin creado por CLI es su usuario.
3. **"Único dispositivo" = una sesión viva por cuenta, ligada a la cookie de dispositivo.** El vínculo es una cookie `HttpOnly`, no un identificador de hardware (spec §3, limitación 7).
4. **"Administrador" = admin global**, creado por CLI; no hay credenciales por defecto. Su segundo factor (RS-01) queda para un parcial posterior por decisión del equipo.
5. **"Registrar eventos" = registros JSON** en la salida de cada servicio (RNF-19). La cadena verificable (RS-22), el registro obligatorio (RS-24) y las alertas en el panel (RS-20) llegan con el servicio de auditoría.
6. **Formatos.** La Actividad 3 admite PNG, JPEG, GIF, MP3, WAV, MP4, PDF, DOCX y TXT. El primer parcial analiza PNG y JPEG; `FORMATS` es el punto de extensión para los demás (RF-19).
7. **Veredictos de `stego`** (RC-03):

| Hallazgo | Veredicto | Respuesta |
|---|---|---|
| Firma, tamaño o decodificación inválidos | `invalida` | `422` con los `motivos` |
| Anomalía estructural (datos al final, metadatos excesivos) | `problema` | `200`; evento `warning` |
| Detector estadístico sobre el umbral, o el análisis supera el tiempo | `revision_manual` | `200`; evento `warning` |
| Nada sospechoso | `limpia` | `200`; evento `info` |

Si coinciden estructura y estadística, gana `problema`.

## 6. Diferencias con la spec que hay que resolver antes de las salas

La Actividad 3 aprobada difiere de la spec rev. 4 en puntos que no afectan al primer parcial:
- **Quién crea y administra las salas.** La Actividad 3 dice que lo hace el administrador (RF-02…RF-08); la spec rev. 4 propone salas con dueño, como en Discord.
- **Formatos.** La Actividad 3 pide 9 formatos con inspección propia (PDF, DOCX, audio y video); la spec solo cubre PNG y JPEG.
- **Inactividad.** La Actividad 3 cierra la conexión del chat a los 15 min sin mensajes (RF-13).
