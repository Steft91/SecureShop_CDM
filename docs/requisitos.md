# Requisitos funcionales y de seguridad — Primer parcial

| | |
|---|---|
| **Fuente** | El enunciado de la Tarea 2 (`Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md`), el resumen del docente y la clase del 22/10/2026 (alcance del primer parcial) |
| **Fecha** | 2026-10-26 (recortado al primer parcial) |
| **Alcance** | Solo el primer parcial: el gateway, `auth` (cuentas, roles, RBAC y JWT) y `stego`, probados con Postman. La lista completa de requisitos del proyecto llegará en un Excel aparte; los requisitos de salas, chat, multimedia, auditoría encadenada y TOTP se agregan cuando el docente defina los parciales 2 y 3 |
| **Uso** | Cada requisito tiene un ID estable (RF-, RS-, RP-, RNF-). Los planes, los tickets y `docs/trazabilidad-riesgos.md` se refieren a ellos |

**Origen** usa estas referencias:
- **¶n:** el párrafo n de la descripción del documento del docente.
- **M-n:** la n-ésima *funcionalidad mínima esperada* de su lista de 16.
- **Clase:** lo que pidió el docente en la clase del 22/10/2026.
- **Equipo:** decisión del equipo.

**Estado:**
- **Planificado:** una tarea del plan lo construye y tiene un test (o una evidencia manual) especificado.
- **Implementado:** el test está en verde. PAR-2 actualiza esta columna al cerrar el parcial.
- **Documental:** el entregable no es código; el archivo ya existe en `docs/`.

---

## 1. Requisitos funcionales

### 1.1 Cuentas, roles y permisos (`auth`)
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-31 | Registrarse con usuario y contraseña; la cuenta nace sin roles | Clase | §9.1 | ATH-2 | `test_registro_crea_cuenta_sin_roles`, `test_r05_registro_con_campo_role_422` | Planificado |
| RF-01 | Iniciar sesión con usuario y contraseña; el login entrega un JWT | ¶2, M-1, Clase | §9.1 | ATH-2 | `test_login_entrega_jwt_y_sesion` | Planificado |
| RF-35 | Consultar la propia cuenta con sus roles y permisos actuales | Clase | §8.1 | ATH-2 | `test_me_y_logout`, `test_verify_devuelve_identidad_y_permisos_actuales` | Planificado |
| RF-02 | Cerrar la sesión: el token queda invalidado | M-14 | §9.1 | ATH-2 | `test_me_y_logout`, `test_jwt_de_sesion_terminada_401` | Planificado |
| RF-17 | Una cuenta se conecta desde un único dispositivo; el login desde otro se rechaza mientras la sesión siga viva | ¶3, M-6 | §9.1 | ATH-2 | `test_r13_login_desde_otro_dispositivo_409` | Planificado |
| RF-19 | Las sesiones vencen por inactividad (30 min) y por tiempo absoluto (8 h) | M-14 | §9.1 | ATH-2 | `test_sesion_inactiva_libera_el_dispositivo`, `test_sesion_vencida_por_tiempo_absoluto_401` | Planificado |
| RF-41 | El admin global se crea por línea de comandos, sin credenciales por defecto | Equipo | §9.1 | ATH-3 | `test_crea_admin_con_argon2id_y_rol_admin`, `test_el_admin_entra_con_su_contraseña` | Planificado |
| RF-32 | El admin global crea roles, les asigna permisos del catálogo y asigna roles a los usuarios | Clase | §9.1 | ATH-4 | `test_crear_rol_con_permisos`, `test_r05_rol_asignado_vale_en_la_siguiente_peticion` | Planificado |

### 1.2 Análisis de imágenes (`stego`)
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-40 | Analizar una imagen con la API de esteganografía usando el token que emite `auth`; la respuesta dice si es inválida, limpia, con problema o para revisión manual | Clase | §9.9, §12.7 | STG-3, GW-1 | `test_imagen_limpia`, `test_r06_archivo_pegado_al_final_es_problema` y la colección de Postman | Planificado |
| RF-25 | Validar cada archivo antes de analizarlo: tipo real, tamaño y decodificación | ¶5, M-11 | §12.1 | STG-2 | `test_r09_contenido_que_no_coincide_con_la_firma`, `test_r09_bomba_de_descompresion_rechazada`, `test_r09_archivo_demasiado_grande` | Planificado |
| RF-27 | Detectar imágenes modificadas con esteganografía | ¶5, M-12, Clase | §12 | STG-1, STG-2 | `test_r06_*` | Planificado |
| RF-29 | Extender los formatos aceptados sin reescribir el análisis | Equipo | §12.1, §12.6 | STG-2 | `test_deteccion_por_firma_ignora_la_extension` | Planificado |

### 1.3 Eventos de seguridad
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-30 | Registrar los eventos relevantes de seguridad (logins, bloqueos, rechazos de permiso, cambios de roles, análisis) como registros JSON en la salida de cada servicio | M-13, ¶5 | §14.2 | FND-4, ATH-2…4, STG-3 | `test_formato_json_de_los_registros` y un `testing.events(caplog, …)` por evento | Planificado |

---

## 2. Requisitos de seguridad

### 2.1 Autenticación, autorización y sesiones
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-01 | Autenticación segura: contraseña con Argon2id, bloqueo tras 5 fallos en 15 min y el mismo error si el usuario no existe | M-1 | §9.1, §11.1 | FND-3, ATH-2 | `test_r04_*`, `test_error_generico_para_clave_mala_y_usuario_inexistente` | Planificado |
| RS-02 | Toda operación se autoriza en el servidor, en cada servicio, por permiso (RBAC) y con los permisos **actuales** del usuario | Zero Trust, M-15, Clase | §4.3, §9.1 | FND-4, ATH-4, STG-3, GW-1 | `test_r05_sin_el_permiso_403_y_se_registra` (shared), `test_r05_sin_el_permiso_403` (stego), `test_r05_rol_asignado_vale_en_la_siguiente_peticion` | Planificado |
| RS-05 | La sesión queda atada al dispositivo y se verifica en **cada** petición | ¶3, M-6 | §9.1 | ATH-2, GW-1 | `test_r13_jwt_con_otra_cookie_de_dispositivo_401` | Planificado |
| RS-06 | Una sola sesión viva por cuenta, garantizada por la BD | ¶3, M-14 | §7.1, §9.1 | ATH-2 | `test_r13_el_indice_unico_impide_dos_sesiones_vivas` | Planificado |
| RS-08 | Un token usado desde otro equipo, o un usuario sin el permiso, se rechazan | ¶3, Zero Trust | §4.3, §9.1 | ATH-2, STG-3 | `test_r13_*`, `test_r05_*` | Planificado |
| RS-35 | Sin escalamiento de privilegios: el registro nunca da roles, los cuerpos rechazan campos de más y el sistema nunca se queda sin admin | Equipo | §8.1, §9.1 | ATH-2, ATH-4 | `test_r05_registro_con_campo_role_422`, `test_r05_cuerpo_con_campos_de_mas_422`, `test_r05_no_se_quita_el_ultimo_admin` | Planificado |
| RS-36 | Token firmado y revocable: JWT RS256 que solo `auth` puede firmar, verificado en cada petición junto con la sesión a la que apunta | Clase | §2, §4.3, §8.1 | ATH-1, ATH-2, GW-1 | `test_alg_none_y_hs256_con_la_clave_publica_se_rechazan`, `test_jwt_alterado_401`, `test_jwt_de_sesion_terminada_401` | Planificado |

### 2.2 Criptografía y gestión de claves
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-13 | Gestión de claves: secretos solo en `/run/secrets`, el JWT nunca se guarda, la cookie de dispositivo y los tokens de servicio se guardan como hash, y cada secreto se puede rotar | ¶4 | §11 | FND-2, FND-6 | `test_secreto_ausente_detiene_el_servicio`, `test_rotar_token_del_gateway_regenera_hash_y_conf` | Planificado |
| RS-14 | Solo TLS 1.3 hacia el cliente; http redirige a https; HSTS | ¶4, M-8 | §13 | GW-1 | Verificación manual de GW-1: TLS 1.2 rechazado, http → 301 | Planificado |
| RS-15 | Justificación documentada de algoritmos, protocolos y gestión de claves | ¶4 | §11 | — | `docs/justificacion-criptografica.md` | Documental |

### 2.3 Análisis de imágenes
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-16 | Carga segura: firma real (*magic bytes*), decodificación segura, tope de tamaño y de píxeles | M-10, M-11 | §12.1 | STG-2 | `test_r09_*` | Planificado |
| RS-18 | Detección de esteganografía (chi², RS y estructura) con umbrales calibrados con imágenes reales | ¶5, M-12 | §12 | STG-1, STG-4 | `test_r06_*`, tabla TPR/FPR en `docs/calibracion-estego.md` | Planificado |

### 2.4 Registros
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-23 | Los registros no contienen contraseñas, claves, tokens ni query strings | M-13 | §14.1 | FND-4, todos | `test_una_linea_por_peticion_sin_query_string`; revisión con `security-auditor` | Planificado |

### 2.5 Zero Trust, mínimo privilegio y diseño seguro
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-25 | Ningún componente es confiable por defecto: `auth_request` a `auth` en cada petición, token de servicio con allowlist y cabeceras de identidad que solo valen si las trae el gateway | Zero Trust | §4.3 | FND-4, ATH-2, STG-3, GW-1 | `test_identidad_solo_vale_si_la_trae_el_gateway`, `test_ruta_interna_respeta_la_allowlist`, `test_r16_verify_solo_para_el_gateway`, `test_r16_solo_acepta_el_token_del_gateway` | Planificado |
| RS-26 | Mínimo privilegio: BD propia de `auth`, rol `auth_app` sin DDL, `cap_drop: ALL`, FS de solo lectura y redes internas | M-15 | §4.5, §7.6 | FND-6, ATH-1 | `test_r11_*` | Planificado |
| RS-27 | Toda entrada se valida: esquema con `extra="forbid"`, longitud, normalización y SQL parametrizado | Zero Trust | §8.1, §15 | todos | `test_politica_de_claves`, `test_usuario_normalizado_en_registro_y_login`, `test_r05_cuerpo_con_campos_de_mas_422`, bandit, CodeQL | Planificado |
| RS-28 | Resistencia a abuso: rate limit en Nginx, tope de registros por IP y de análisis por minuto por usuario | (R10) | §13, §9.9 | GW-1, ATH-2, STG-3 | `test_r10_tope_de_registros_por_ip`, `test_r10_limite_de_analisis_por_minuto` | Planificado |
| RS-29 | Errores genéricos al cliente; el detalle va solo a los registros; todo falla cerrado | Secure by Design | §15 | FND-4 | `test_errores_genericos` | Planificado |

### 2.6 Normas y enfoques
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-30 | **Secure by Design**: los controles forman parte de la arquitectura desde el diseño | ¶ enfoques | §4, §16.3 | FND-1 | `docs/cumplimiento-normativo.md` §4 | Documental |
| RS-31 | **Zero Trust**: ninguna petición, dispositivo, sesión o servicio es confiable por defecto | ¶ enfoques | §4.3 | FND-4, GW-1 | `docs/cumplimiento-normativo.md` §3 | Documental |
| RS-32 | **Shift Left**: modelo de amenazas, revisión de código, pruebas y detección de vulnerabilidades desde la primera tarea | ¶ enfoques, M-16 | §16.5, §17 | FND-1, FND-7 | CI (ruff, bandit, pip-audit, CodeQL, gitleaks) | Planificado |
| RS-33 | **ISO/IEC 27001:2022**: controles del Anexo A relacionados con riesgos y mecanismos | ¶ normas | — | FND-1 | `docs/cumplimiento-normativo.md` §1 y la columna ISO de `docs/trazabilidad-riesgos.md` | Documental |
| RS-34 | **ISO/IEC 27034**: marco normativo de la aplicación (ONF/ANF/ASC) y verificación de los controles | ¶ normas | — | FND-1 | `docs/cumplimiento-normativo.md` §2 | Documental |

---

## 3. Requisitos de proceso y entregables

| ID | Requisito | Origen | Dónde está | Estado |
|---|---|---|---|---|
| RP-01 | Análisis de activos, amenazas, vulnerabilidades y riesgos | ¶ proyecto | Tarea 2 (Tablas 1–4) y R16 (spec §16.3) | Documental |
| RP-02 | Requisitos funcionales y de seguridad definidos | ¶ proyecto | Este documento | Documental |
| RP-03 | Arquitectura diseñada | ¶ proyecto | `docs/specs/2026-10-12-chat-seguro-design.md` (rev. 4) | Documental |
| RP-04 | Aplicación implementada y funcional | Resultado esperado | `docs/plans/` y `docs/tickets/parcial-1/` → `services/`, `gateway/` | Planificado |
| RP-05 | Pruebas que demuestren la eficacia de los controles | ¶ proyecto | Un `test_rNN_*` por riesgo y la sección de evidencias de `docs/informe-parcial-1.md` | Planificado |
| RP-06 | Justificar algoritmos, protocolos, gestión de claves y controles | ¶4 | `docs/justificacion-criptografica.md` | Documental |
| RP-07 | Demostrar cómo los controles ISO se relacionan con riesgos y mecanismos | ¶ normas | `docs/cumplimiento-normativo.md` y `docs/trazabilidad-riesgos.md` | Documental |
| RP-08 | Documentación técnica que evidencie ISO 27001, ISO 27034, Zero Trust, Secure by Design y Shift Left | Resultado esperado | `docs/cumplimiento-normativo.md` | Documental |
| RP-10 | Informe del primer parcial: descripción de la aplicación, cómo se construyó, tipo de API (REST), tecnologías, bibliotecas y herramientas, e integración con `auth` | Clase | `docs/informe-parcial-1.md` (PAR-2) | Planificado |
| RP-11 | Demostración en vivo del primer parcial: la API de esteganografía funcionando con el token de `auth` | Clase | `docs/postman/parcial-1.postman_collection.json` (PAR-1) y `docs/demo-parcial-1.md` (PAR-3) | Planificado |

### 3.1 Requisitos no funcionales de la Actividad 3 que se adoptan

Los IDs RNF y A3- son los de la transcripción de la Actividad 3 que hizo el equipo el 20/10. Los demás no entran en el primer parcial (spec §22.1).

| ID | Requisito | Plan | Verificación | Estado |
|---|---|---|---|---|
| RNF-10 | Cobertura de líneas ≥ 80 % por servicio | FND-7 | CI (`--cov-fail-under=80`) | Planificado |
| RNF-11 | Complejidad ciclomática ≤ 10 por función | FND-1, STG-1 | CI (`ruff` con `C90`) | Planificado |
| RNF-18 | Un registro JSON por petición | FND-4, GW-1 | `test_una_linea_por_peticion_sin_query_string`; curl de GW-1 | Planificado |
| RNF-19 | Id de correlación de punta a punta, del gateway a los eventos | FND-4, GW-1 | `test_el_id_del_gateway_llega_al_codigo_y_a_los_eventos`, `test_id_ausente_o_invalido_se_reemplaza` | Planificado |
| A3-RS-32 | Cambios controlados: PR con aprobación, plantilla y CI en verde | FND-1, FND-7 | Regla de `main` en GitHub | Planificado |

---

## 4. Decisiones de interpretación

1. **"Usuario" = cuenta registrada.** El registro es abierto y la cuenta nace sin permisos: los da el admin global con un rol.
2. **"Único dispositivo" = una sesión viva por cuenta, ligada a la cookie de dispositivo.** Se rechaza el login desde otro dispositivo. El vínculo es una cookie `HttpOnly`, no un identificador de hardware; es una limitación declarada (spec §3, limitación 7).
3. **"Agregarle propiedades al rol"** (clase del 22/10) = asignarle permisos del catálogo fijo: `users:manage`, `roles:manage` y `stego:analyze`. El único rol de fábrica es `admin`, con los tres.
4. **"Administrador" = admin global**, creado por CLI. No hay credenciales por defecto.
5. **"Multimedia" = imágenes PNG y JPEG.** `FORMATS` es el punto de extensión (RF-29).
6. **"Registrar eventos" = registros JSON** en la salida de cada servicio (`docker compose logs`). La bitácora encadenada y su consulta quedan para después.
7. **Veredictos de `stego`** (RF-40):

| Hallazgo | Veredicto | Respuesta |
|---|---|---|
| Firma, tamaño o decodificación inválidos | `invalida` | `422` con los `motivos` |
| Anomalía estructural (datos al final, metadatos excesivos) | `problema` | `200`; evento `warning` |
| Detector estadístico sobre el umbral, o el análisis supera el tiempo | `revision_manual` | `200`; evento `warning` |
| Nada sospechoso | `limpia` | `200`; evento `info` |

Si coinciden estructura y estadística, gana `problema`.

---

## 5. Fuera del primer parcial

No se construyen ahora: salas, chat y cifrado de mensajes, subida y descarga de archivos, ClamAV, el servicio `audit` con su cadena verificable, el TOTP de los admins, la rotación de la KEK, la suspensión de cuentas, el frontend y el despliegue en VPS. Están diseñados en la spec y vuelven como requisitos cuando el docente defina los parciales 2 y 3.
