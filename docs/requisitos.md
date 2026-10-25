# Requisitos funcionales y de seguridad — Salas de Chat Seguras

| | |
|---|---|
| **Fuente** | `PROYECTO INTEGRADOR - RESUMEN.docx` (resumen del docente), el enunciado de la Tarea 2 (`Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md`) y la clase del 22/10/2026 (alcance del primer parcial) |
| **Fecha** | 2026-10-13 (spec rev. 3) · actualizado el 2026-10-25 (spec rev. 4) |
| **Uso** | Cada requisito tiene un ID estable (RF-, RS-, RP-). El spec, el plan, los tickets y `docs/trazabilidad-riesgos.md` se refieren a ellos. |

**Origen** usa estas referencias:
- **¶n:** el párrafo n de la descripción del documento del docente.
- **M-n:** la n-ésima *funcionalidad mínima esperada* de su lista de 16.
- **Clase:** lo que pidió el docente en la clase del 22/10/2026.
- **Equipo:** decisión del equipo, en general tomada al comparar el diseño con una propuesta de roles USER/ADMIN.

**Estado:**
- **Cubierto:** el spec lo define, una tarea del plan lo construye y un test (o evidencia manual) lo verifica.
- **Ajustado:** el análisis encontró una brecha y se corrigió en el spec y en el plan (ver §5).
- **Documental:** el entregable no es código; el archivo ya existe en `docs/`.

Nada está implementado todavía: "Cubierto" significa *diseñado, planificado y con test especificado*. La columna de verificación pasa a "en verde" cuando se ejecute el plan.

---

## 1. Requisitos funcionales

### 1.1 Cuentas, roles y permisos
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-01 | Iniciar sesión con usuario y contraseña (y TOTP si la cuenta tiene un permiso de admin); el login entrega un JWT | ¶2, M-1, Clase | §9.1 | ATH-2, ATH-3 | `test_login_entrega_jwt_y_sesion`, `test_r04_*` | **Ajustado (B-10)** |
| RF-02 | Cerrar la sesión: el token queda invalidado y se cierran las conexiones del usuario | M-14 | §9.1, §8.1 | ATH-2 | `test_logout_invalida_el_token` | Cubierto |
| RF-17 | Una cuenta se conecta desde un único dispositivo; el login desde otro se rechaza mientras la sesión siga viva | ¶3, M-6 | §9.1 | ATH-2 | `test_r13_login_desde_otro_dispositivo_409` (+ e2e) | **Ajustado (B-10)** |
| RF-31 | Registrarse con usuario y contraseña; el registro siempre da el rol `user` | Clase | §9.1 | ATH-2 | `test_registro_da_solo_el_rol_user`, `test_r05_registro_con_campo_role_422` | **Ajustado (B-10)** |
| RF-32 | El admin global crea roles, les asigna permisos del catálogo y asigna roles a los usuarios | Clase | §9.1 | ATH-4 | `test_crear_rol_con_permisos`, `test_r05_rol_asignado_vale_en_la_siguiente_peticion` | **Ajustado (B-10)** |
| RF-33 | El admin global suspende y reactiva cuentas; la suspensión corta el acceso al instante | Equipo | §9.1 | ATH-5 | `test_suspension_corta_el_acceso`, `test_suspension_con_fecha_vence_sola` | **Ajustado (B-12)** |
| RF-34 | Cambiar la propia contraseña | Equipo | §9.1 | ATH-5 | `test_cambio_de_contrasena_termina_la_sesion` | **Ajustado (B-12)** |
| RF-35 | Consultar la propia cuenta con sus roles y permisos actuales ("rol activo") | Clase | §8.1 | ATH-2 | `test_me_devuelve_permisos_actuales` | **Ajustado (B-10)** |

### 1.2 Salas
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-03 | Crear una sala con identificador único (el duplicado se rechaza; mayúsculas y espacios se normalizan). Lo hace cualquier usuario con `rooms:create`, con un máximo de 2 salas activas por persona | ¶2, M-2, M-4, Equipo | §7.2, §9.2 | ROOM-1, ROOM-2 | `test_codigo_de_sala_normalizado` (incluye el 409 por duplicado), `test_r15_maximo_dos_salas_por_dueno` | **Ajustado (B-11)** |
| RF-04 | Cada sala tiene una clave de acceso propia e independiente | ¶2, M-4 | §7.2, §8.1 | ROOM-2 | `test_r01_clave_de_sala_guardada_con_argon2id`, `test_r08_clave_de_sala_debil_rechazada` | Cubierto |
| RF-05 | Definir y cambiar el número máximo de participantes (2–50, nunca menor a los miembros actuales) | ¶2, M-3 | §7.2, §8.1 | ROOM-2 | `test_patch_cambia_modo_y_valida_cupo` | Cubierto |
| RF-06 | Definir el tipo de sala: texto, multimedia o ambos | ¶2, M-5 | §7.2 | ROOM-2 | `test_patch_cambia_modo_y_valida_cupo`, `test_texto_en_sala_solo_multimedia_4403` | Cubierto |
| RF-07 | Consultar las salas: *Mis salas* para el usuario y todas, solo con metadatos, para el admin global | M-2 | §8.1 | ROOM-2, FE-2, FE-5 | `test_mis_salas`, `test_admin_lista_salas_sin_mensajes` | **Ajustado (B-11)** |
| RF-08 | Modificar una sala (clave, cupo, tipo): el dueño; el admin global, todo menos la clave | M-2, M-3 | §8.1, §9.3 | ROOM-2, **FE-3** | `test_patch_cambia_modo_y_valida_cupo`, `test_r05_admin_no_cambia_la_clave_ajena`; formulario *Editar* en FE-3 (verificación manual) | **Ajustado (B-05, B-14)** |
| RF-09 | Cerrar una sala (dueño o admin global): se cierran sus conexiones y no admite nuevos ingresos | M-2 | §8.1, §9.3 | ROOM-2, ROOM-4, **FE-3** | `test_cerrar_sala_corta_las_conexiones`, `test_sala_cerrada_no_admite_ingresos` | **Ajustado (B-06)** |
| RF-36 | Ceder la sala a otro miembro | Equipo | §9.3 | ROOM-4 | `test_ceder_la_sala`, `test_ceder_a_quien_ya_tiene_dos_salas_409` | **Ajustado (B-11)** |

### 1.3 Membresía y conexiones
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-13 | Unirse a una sala la primera vez con identificador + clave + alias; después, abrirla desde *Mis salas* sin la clave | ¶3, M-7, Equipo | §9.2 | ROOM-3, FE-2 | `test_ingreso_correcto`, `test_volver_sin_clave` | **Ajustado (B-11)** |
| RF-14 | Un ID o una clave inválidos se rechazan con un mensaje genérico | ¶3 | §9.2, §15 | ROOM-3 | `test_error_generico_para_clave_mala_y_sala_inexistente` | Cubierto |
| RF-15 | Si la sala está llena, el ingreso se rechaza | M-3 | §9.2 | ROOM-3 | `test_sala_llena_409`, `test_r15_*` | Cubierto |
| RF-16 | Una sala cerrada no admite ingresos | M-2 | §9.2 | ROOM-3 | `test_sala_cerrada_no_admite_ingresos` | Cubierto |
| RF-18 | Salir de la sala y liberar el lugar; el dueño debe cederla antes | M-14 | §9.2 | ROOM-3, FE-2 | `test_salir_libera_el_lugar`, `test_el_dueno_no_sale_sin_ceder` | Cubierto |
| RF-19 | Las conexiones inactivas se cierran solas y las sesiones vencen por inactividad y por tiempo absoluto | M-14 | §9.1, §9.4 | ATH-2, CHAT-4 | `test_sesion_inactiva_401`, `test_inactividad_cierra_4410` | Cubierto |

### 1.4 Moderación
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-37 | El dueño expulsa a un miembro, con veto opcional por un tiempo, y puede levantar el veto | Equipo | §9.3 | ROOM-4, FE-3 | `test_expulsar_con_veto`, `test_r08_el_veto_se_revisa_despues_de_la_clave` | **Ajustado (B-12)** |
| RF-38 | El dueño silencia a un miembro por un tiempo; el servidor rechaza sus mensajes e imágenes | Equipo | §9.3, §9.5, §9.6 | ROOM-4, CHAT-3, MED-2 | `test_silenciado_no_escribe`, `test_silenciado_no_sube` | **Ajustado (B-12)** |
| RF-39 | Cada miembro borra sus mensajes y el dueño borra los de otros; todos ven "mensaje eliminado" en tiempo real | Equipo | §9.5 | CHAT-3, FE-2 | `test_borrar_mensaje_propio`, `test_r14_borrar_ajeno_sin_ser_dueno_4403` | **Ajustado (B-12)** |

### 1.5 Mensajería y multimedia
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-20 | Intercambiar mensajes de texto en tiempo real dentro de la sala | ¶1 (sala de chat) | §9.5 | CHAT-3, FE-2 | `test_hello_firmado_y_mensaje_cifrado`, e2e | Cubierto |
| RF-21 | Ver quién se conecta y se desconecta, y el historial reciente al conectarse | ¶1 | §9.5 | CHAT-3 | `test_historial_al_entrar_y_cifrado_en_reposo`, `test_el_historial_incluye_los_archivos` | Cubierto |
| RF-22 | La sala respeta su tipo: solo texto rechaza archivos; solo multimedia rechaza texto | ¶2, M-5 | §9.5, §9.6 | CHAT-3, MED-2 | `test_sala_de_solo_texto_no_acepta_archivos` (media), `test_texto_en_sala_solo_multimedia_4403` (chat) | Cubierto |
| RF-23 | Subir archivos multimedia (imágenes PNG/JPEG) a las salas que los permitan | M-10 | §9.6 | MED-3, FE-4 | `test_imagen_limpia_se_sanitiza_y_se_publica` (`test_r06_pipeline.py`) | Cubierto |
| RF-24 | Ver y descargar las imágenes compartidas en la sala | M-10 | §9.7 | CHAT-4, MED-3, FE-4 | `test_r12_descarga_con_firma_valida`, `test_archivo_publicado_llega_con_url_firmada_por_destinatario` | Cubierto |
| RF-25 | Validar cada archivo antes de compartirlo (tipo real, tamaño, decodificación) | ¶5, M-11 | §12.1 | STG-1, MED-3 | `test_r09_formato_no_permitido`, `test_r09_firma_que_no_coincide_con_el_contenido`, `test_r09_bomba_de_descompresion`, `test_r09_archivo_demasiado_grande` | Cubierto |
| RF-26 | Analizar cada archivo con un antimalware | ¶5, M-11 | §9.6 | MED-2 | `test_r09_malware_rechazado_con_alerta_critica`; `test_r09_eicar_detectado_por_clamav_real` (marcador `clamav`) | Cubierto |
| RF-27 | Detectar archivos sospechosos o modificados con esteganografía | ¶5, M-12, Clase | §12 | STG-2 | `test_r06_*` | Cubierto |
| RF-28 | Aplicar una política definida: cuarentena, rechazo o sanitización, e informar a quien subió | ¶5 | §9.6, §12.7 | MED-3 | `test_r06_pipeline.py`, `test_r09_rechazos.py` | Cubierto |
| RF-29 | Extender los formatos aceptados sin reescribir el pipeline | (decisión del equipo) | §12.1, §12.6 | STG-1 | `test_deteccion_por_firma_*` | Cubierto |
| RF-40 | Analizar una imagen con la API de esteganografía usando el token que emite `auth`; la respuesta dice si es inválida, limpia, con problema o para revisión manual | Clase | §9.9, §12.7 | STG-3 | `test_analyze_*` y la colección de Postman del parcial | **Ajustado (B-13)** |

### 1.6 Auditoría y supervisión
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RF-10 | Consultar los eventos de seguridad y las alertas (admin global con `audit:read`) | M-13, ¶5 | §14.3 | AUD-3, FE-5 | `test_listado_filtra_por_severidad_y_pagina`, `test_verify_ok_y_luego_roto` | Cubierto |
| RF-11 | Ver una alerta visible cuando aparece un evento `warning` o `critical` nuevo | ¶5 | §14.3 | **FE-5** | verificación manual (FE-5) y e2e (alerta en la API) | **Ajustado (B-07)** |
| RF-12 | Revisar la cuarentena: listar con el veredicto, liberar o eliminar (admin global con `quarantine:manage`) | ¶5 | §9.8 | MED-4, FE-5 | `test_cuarentena.py` | Cubierto |
| RF-30 | Registrar los eventos y actividades relevantes de seguridad | M-13, ¶5 | §14.2 | AUD-1…AUD-3, todos los servicios | `test_eventos_encadenados_y_verificables` y un `peers.events(...)` por rechazo en cada servicio | Cubierto |

---

## 2. Requisitos de seguridad

### 2.1 Autenticación, autorización y sesiones
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-01 | Autenticación segura: contraseña con Argon2id, bloqueo y retraso progresivo, TOTP obligatorio para todo permiso de admin y `sid` nuevo al pasar a la sesión completa | M-1 | §9.1, §11.1 | ATH-2, ATH-3 | `test_r04_*`, `test_r04_permiso_de_admin_sin_totp_no_vale` | **Ajustado (B-10)** |
| RS-02 | Toda operación se autoriza en el servidor, en cada servicio, por permiso (RBAC) y con los permisos **actuales** del usuario | Zero Trust, M-15, Clase | §4.3, §9.1 | FND-4, ATH-4, GW-1 | `test_r05_sin_el_permiso_403` (auth, rooms, media, stego, audit), `test_r05_rol_asignado_vale_en_la_siguiente_peticion`, e2e | **Ajustado (B-10)** |
| RS-03 | La clave de sala se guarda solo como hash Argon2id con sal; política de claves mínimas | ¶3 | §7.2, §8.1 | ROOM-2 | `test_r01_clave_de_sala_guardada_con_argon2id`, `test_politica_de_claves` | Cubierto |
| RS-04 | El primer ingreso exige ID + clave y limita los intentos por IP, usuario y sala | ¶3, M-7 | §9.2 | ROOM-3 | `test_r08_*` | Cubierto |
| RS-05 | La sesión de la cuenta queda atada al dispositivo y se verifica en **cada** request | ¶3, M-6 | §9.1 | ATH-2, GW-1 | `test_r13_jwt_con_otra_cookie_de_dispositivo_401` (+ e2e) | **Ajustado (B-10)** |
| RS-06 | Se controlan las sesiones activas: una sesión por cuenta (índice único), cupo atómico de miembros, una conexión por usuario y sala, expiración y reconciliación | ¶3, M-14 | §7.1, §7.2, §9.1–§9.5 | ATH-2, ROOM-3, CHAT-3, CHAT-4 | `test_r13_*`, `test_r15_*`, `test_segunda_conexion_del_mismo_usuario_reemplaza_a_la_primera` | Cubierto |
| RS-07 | Cierre seguro: logout, suspensión, salida, expulsión y cierre de sala invalidan el acceso al instante, cierran las conexiones y se auditan | M-14 | §9.1, §9.4 | ATH-2, ATH-5, ROOM-3, ROOM-4, CHAT-4 | `test_logout_invalida_el_token`, `test_suspension_corta_el_acceso`, `test_expulsar_cierra_con_4411`, `test_cerrar_sala_corta_las_conexiones` | Cubierto |
| RS-08 | Un token copiado a otro equipo, o un usuario sin el permiso, se rechazan | ¶3, Zero Trust | §4.3, §9.1 | ATH-2, E2E-1 | `test_r13_*`, `test_r05_*`, e2e | Cubierto |
| RS-35 | Sin escalamiento de privilegios: el registro nunca da `admin`, los cuerpos rechazan campos de más, el sistema nunca se queda sin admin y el admin global no cambia la clave de salas ajenas | Equipo | §8.1, §9.1, §9.3 | ATH-2, ATH-4, ROOM-2 | `test_r05_registro_con_campo_role_422`, `test_r05_no_se_quita_el_ultimo_admin`, `test_r05_admin_no_cambia_la_clave_ajena` | **Ajustado (B-10, B-14)** |
| RS-36 | Token firmado y revocable: JWT RS256 que solo `auth` puede firmar, verificado en cada request junto con la sesión a la que apunta | Clase | §2, §4.3, §8.1 | ATH-2, GW-1 | `test_jwt_alterado_401`, `test_jwt_de_sesion_terminada_401` | **Ajustado (B-10)** |
| RS-37 | Privacidad de las salas frente al admin global: no accede a los mensajes de salas en las que no es miembro | Equipo, ISO 27001 A.5.34 | §3 (limitación 8), §9.3 | ROOM-2, CHAT-3 | `test_admin_lista_salas_sin_mensajes`, `test_r05_admin_no_cambia_la_clave_ajena`; no existe ninguna ruta que devuelva mensajes fuera del WS | **Ajustado (B-14)** |

### 2.2 Criptografía y gestión de claves
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-09 | **Confidencialidad** de los mensajes en tránsito: TLS 1.3 hasta el gateway y AES-256-GCM por conexión sobre ECDH efímero | ¶4, M-8 | §10 | FND-2, CHAT-3, FE-1 | `test_vectores_reproducen_handshake_y_tramas` (pytest) y `crypto.test.ts` (vitest), `test_hello_firmado_y_mensaje_cifrado` | Cubierto |
| RS-10 | **Integridad** de los mensajes: AEAD con AAD (sala, sesión, dirección, `seq`) y anti-replay | ¶4, M-9 | §10.2 | FND-2, CHAT-3 | `test_r14_replay_cierra_4408`, `test_r07_trama_alterada_cierra_4400_con_alerta_critica` | Cubierto |
| RS-11 | **Autenticidad**: el servidor se autentica con un *hello* firmado (ECDSA), el remitente sale de la cuenta verificada y el `Origin` se valida | ¶4 | §10.1, §9.5 | FND-2, CHAT-3, FE-1 | `test_r07_origin_ajeno_se_cierra_con_4403`, `test_r14_el_remitente_sale_de_la_identidad_verificada`, `test_vector_de_firma_del_hello` | Cubierto |
| RS-12 | **Todos** los datos de la sala protegidos en reposo: mensajes (DEK por sala) **y archivos (DEK por archivo)** | ¶4 ("toda la información") | §11.2, §9.6 | CHAT-2, **MED-1, MED-3, MED-4** | `test_r02_mensajes_cifrados_en_reposo_y_legibles` (chat), `test_r02_archivos_cifrados_en_reposo` (media) | **Ajustado (B-04)** |
| RS-13 | Gestión de claves: secretos solo en `/run/secrets`, KEK/DEK, el JWT nunca se guarda, la cookie de dispositivo se guarda como hash, rotación de cada clave | ¶4 | §11 | FND-6, ATH-6, CHAT-2, **MED-4** | `test_secreto_ausente_detiene_el_servicio`, `test_r02_rotar_la_kek_mantiene_el_totp_legible`, `test_r02_rotar_la_kek_mantiene_el_historial`, `test_r02_rotar_la_dek_de_una_sala`, `test_r02_rotar_la_kek_de_media` | Cubierto (media: B-04) |
| RS-14 | Solo TLS 1.3 hacia el cliente; `ws://` no existe; HSTS | ¶4, M-8 | §13 | GW-1, E2E-1 | e2e: TLS 1.2 rechazado, http → 301 | Cubierto |
| RS-15 | Justificación documentada de algoritmos, protocolos y gestión de claves | ¶4 | §10, §11 | — | `docs/justificacion-criptografica.md` | Documental (B-02) |

### 2.3 Contenido multimedia
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-16 | Carga segura: miembro de la sala, modo de sala, sin silencio, tope de tamaño y de frecuencia, firma real (*magic bytes*), decodificación segura y tope de píxeles | M-10, M-11 | §9.6, §12.1 | STG-1, MED-2, MED-3 | `test_r09_*` | Cubierto |
| RS-17 | Transferencia segura: URL firmada de 60 s ligada al usuario, membresía verificada en la descarga, 404 genérico, sin listado, nombres aleatorios, `nosniff` y `no-store` | M-10 | §9.7 | CHAT-4, MED-3 | `test_r12_*` | Cubierto |
| RS-18 | Detección de esteganografía (chi², RS, estructura) con umbrales calibrados con imágenes reales | ¶5, M-12 | §12 | STG-2, STG-4, E2E-3 | `test_r06_*`, tabla TPR/FPR en `docs/calibracion-estego.md` | Cubierto |
| RS-19 | Un archivo sospechoso nunca se publica; la sanitización destruye payloads LSB aunque no se detecten | ¶5 | §9.6, §12.5 | STG-3, MED-3 | `test_r06_sanitizar_png_destruye_el_lsb_y_quita_chunks`, `test_reenvio_de_imagen_sanitizada_no_va_a_cuarentena` | Cubierto |
| RS-20 | Alerta ante estego, malware o manipulación (evento `warning`/`critical` en auditoría y aviso en el panel) | ¶5 | §14.2, §14.3 | MED-3, AUD-3, **FE-5** | `peers.events("file.quarantined")`, e2e | **Ajustado (B-07)** |
| RS-21 | El análisis falla cerrado: sin ClamAV o sin `stego` no se acepta nada | ¶5, M-11 | §9.6 | MED-2, MED-3 | `test_r09_clamav_caido_falla_cerrado`, `test_r09_stego_caido_responde_503` | Cubierto |

### 2.4 Auditoría y trazabilidad
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-22 | Registro de eventos con integridad verificable (cadena SHA-256; el rol de la app solo hace INSERT/SELECT) | M-13 | §14 | AUD-1, AUD-2, AUD-3 | `test_r03_rol_app_no_puede_alterar_ni_borrar`, `test_r03_alteracion_detectada_por_verify` | Cubierto |
| RS-23 | Los registros no contienen contraseñas, claves, tokens ni cuerpos de mensajes | M-13 | §14.1 | AUD-2, todos | revisión con `security-auditor` y regla `.claude/rules/security.md` (sin test automatizado; `test_detalles_con_nan_se_rechazan` cubre solo la forma de `details`) | Cubierto |
| RS-24 | Si la auditoría no responde, las operaciones que otorgan acceso fallan cerradas; las que lo quitan siguen | M-13 | §14.4 | FND-4 | `test_evento_obligatorio_sin_audit_da_503`, `test_evento_no_obligatorio_cae_a_stdout`, `test_sin_audit_el_login_se_revierte_con_503`, `test_sin_audit_el_ingreso_se_revierte` | Cubierto |

### 2.5 Zero Trust, mínimo privilegio y diseño seguro
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-25 | Ningún componente es confiable por defecto: `auth_request` a `auth` por request, token de servicio por llamador con allowlist, cabeceras de identidad sobrescritas | Zero Trust (¶ enfoques) | §4.3 | FND-4, GW-1 | `test_identidad_solo_vale_si_la_trae_el_gateway`, `test_ruta_interna_respeta_la_allowlist`, `test_r16_*`, e2e | Cubierto |
| RS-26 | Mínimo privilegio en datos y ejecución: BD y roles por servicio, `app` sin DDL, `cap_drop: ALL`, FS de solo lectura, redes internas | M-15 | §4.5, §7.6 | FND-6, `*-1` | `test_r11_*` | Cubierto |
| RS-27 | Toda entrada se valida (esquema con `extra="forbid"`, longitud, normalización, parámetros SQL) | Zero Trust ("validada") | §8.1, §15 | todos | `test_politica_de_claves`, `test_alias_invalido_422`, `test_caracteres_de_control_rechazados`, `test_r05_registro_con_campo_role_422`, bandit, CodeQL | Cubierto |
| RS-28 | Resistencia a abuso: rate limit perimetral y por conexión, tope de tamaño de trama y de conexiones, tope de registros y de análisis | (R10) | §13, §9.5, §9.9 | GW-1, CHAT-3, ATH-2, STG-3 | `test_r10_*` | Cubierto |
| RS-29 | Errores genéricos al cliente; el detalle va solo a auditoría; todo falla cerrado | Secure by Design | §15 | FND-4 | `test_errores_genericos` | Cubierto |

### 2.6 Normas y enfoques
| ID | Requisito | Origen | Spec | Plan | Verificación | Estado |
|---|---|---|---|---|---|---|
| RS-30 | **Secure by Design**: los controles forman parte de la arquitectura desde la primera revisión | ¶ enfoques | §4, §16.3 | FND-1 | `docs/cumplimiento-normativo.md` §4 | Documental (B-03) |
| RS-31 | **Zero Trust**: ninguna petición, dispositivo, sesión o servicio es confiable por defecto | ¶ enfoques | §4.3 | GW-1, FND-4 | `docs/cumplimiento-normativo.md` §3 | Documental (B-03) |
| RS-32 | **Shift Left**: modelo de amenazas, revisión de código, pruebas y detección de vulnerabilidades desde la primera tarea | ¶ enfoques, M-16 | §16.5, §17 | FND-1, FND-7 | CI (ruff, bandit, pip-audit, npm audit, **CodeQL, gitleaks**) | **Ajustado (B-03)** |
| RS-33 | **ISO/IEC 27001:2022**: controles del Anexo A relacionados con riesgos y con mecanismos | ¶ normas | — | FND-1 | `docs/cumplimiento-normativo.md` §1 + columna ISO de `docs/trazabilidad-riesgos.md` | Documental (B-01) |
| RS-34 | **ISO/IEC 27034**: marco normativo de la aplicación (ONF/ANF/ASC) y verificación de los controles | ¶ normas | — | FND-1, E2E-3 | `docs/cumplimiento-normativo.md` §2 | Documental (B-01) |

---

## 3. Requisitos de proceso y entregables

| ID | Requisito | Origen | Dónde está | Estado |
|---|---|---|---|---|
| RP-01 | Análisis de activos, amenazas, vulnerabilidades y riesgos | ¶ proyecto | Tarea 2 (Tablas 1–4) + R16 (spec §16.3) | Cubierto |
| RP-02 | Requisitos funcionales y de seguridad definidos | ¶ proyecto | Este documento | Documental |
| RP-03 | Arquitectura diseñada | ¶ proyecto | `docs/specs/2026-10-12-chat-seguro-design.md` (rev. 4) | Cubierto |
| RP-04 | Aplicación implementada y funcional | Resultado esperado | `docs/plans/` y `docs/tickets/` → `services/`, `gateway/`, `frontend/` | Plan listo; sin ejecutar |
| RP-05 | Pruebas que demuestren la eficacia de los controles | ¶ proyecto, resultado | Tests por riesgo + e2e + `docs/informe-pruebas.md` (se genera en E2E-3) | **Ajustado (B-08)** |
| RP-06 | Justificar algoritmos, protocolos, gestión de claves y controles | ¶4 | `docs/justificacion-criptografica.md` | Documental |
| RP-07 | Demostrar cómo los controles ISO se relacionan con riesgos y mecanismos | ¶ normas | `docs/cumplimiento-normativo.md` + `docs/trazabilidad-riesgos.md` | Documental |
| RP-08 | Documentación técnica que evidencie ISO 27001, ISO 27034, Zero Trust, Secure by Design y Shift Left | Resultado esperado | `docs/cumplimiento-normativo.md` | Documental |
| RP-09 | Demostrar protección de comunicaciones, control de accesos, gestión de sesiones y detección de multimedia manipulada | Resultado esperado | `docs/demo.md` (E2E-3) | Cubierto |
| RP-10 | Informe final del primer parcial: descripción de la aplicación, cómo se construyó, tipo de API (REST), tecnologías, bibliotecas y herramientas, e integración con `auth` | Clase | `docs/informe-parcial-1.md` (tickets DOC del parcial) | **Ajustado (B-13)** |
| RP-11 | Demostración en vivo del primer parcial: la API de esteganografía funcionando con el token de `auth` | Clase | `docs/postman/parcial-1.postman_collection.json` + guion `docs/demo-parcial-1.md` | **Ajustado (B-13)** |

---

## 4. Decisiones de interpretación

1. **"Usuario" = cuenta registrada** (desde la rev. 4). El **alias** es el nombre visible dentro de cada sala; queda fijo mientras la persona sea miembro.
2. **"Único dispositivo" = una sesión activa por cuenta, ligada a la cookie de dispositivo.** Se rechaza el login desde otro dispositivo. El vínculo es una cookie `HttpOnly`, no un identificador de hardware; es una limitación declarada (spec §3, limitación 7).
3. **"Multimedia" = imágenes PNG y JPEG** por ahora. `FORMATS` es el punto de extensión (RF-29).
4. **"Cierre de sala" = `DELETE /api/rooms/{id}`** (`active=false`), que pueden hacer el dueño y el admin global: cierra las conexiones y no admite más ingresos. El código no se reutiliza. En la UI se llama *Cerrar sala*.
5. **"Alertas"** = eventos `warning`/`critical` en `audit`, más un aviso visible en el panel del admin (B-07).
6. **"Agregarle propiedades al rol"** (clase del 22/10) = asignarle permisos del catálogo fijo (spec §9.1).
7. **"Administrador"** tiene dos niveles: el **dueño** administra su sala y el **admin global** administra la plataforma sin leer conversaciones.
8. **Política ante archivos** (RF-28):

| Hallazgo | Veredicto de `stego` | Política | Quién ve qué |
|---|---|---|---|
| Firma, tamaño o decodificación inválidos | `invalida` | **Rechazo** (no se guarda) | Usuario: "archivo no permitido". Auditoría: `warning` |
| Malware (ClamAV) | — | **Rechazo** + alerta crítica | Usuario: "archivo no permitido". Auditoría: `critical` |
| Anomalía estructural (datos al final, metadatos excesivos) | `problema` | **Cuarentena** (no se publica) | Usuario: "archivo retenido para revisión". Admin global: lista con veredicto; liberar (sanitiza y publica) o eliminar |
| Detector estadístico sobre el umbral | `revision_manual` | **Cuarentena** | Igual que la fila anterior |
| Limpio | `limpia` | **Sanitización** y publicación | Sala: imagen con URL firmada |

---

## 5. Análisis de cumplimiento: brechas y cómo se cerraron

El spec rev. 2 y el plan cubrían los 16 riesgos y casi todas las funcionalidades mínimas. El documento del docente agrega los enfoques normativos (ISO 27001/27034, Zero Trust, Secure by Design, Shift Left) y exige **evidencia documentada** (B-01…B-09, rev. 3). La clase del 22/10 pidió cuentas con roles, JWT y una API de esteganografía, y la comparación con una propuesta de roles USER/ADMIN mostró lo que faltaba (B-10…B-14, rev. 4).

| ID | Brecha | Requisito | Corrección |
|---|---|---|---|
| B-01 | Ninguna tabla relacionaba controles ISO/IEC 27001 y 27034 con riesgos y mecanismos | RS-33, RS-34, RP-07 | `docs/cumplimiento-normativo.md`; columna *ISO 27001* en `docs/trazabilidad-riesgos.md` (FND-1) |
| B-02 | Los algoritmos y la gestión de claves estaban descritos pero no *justificados* en un documento entregable | RS-15, RP-06 | `docs/justificacion-criptografica.md` |
| B-03 | Zero Trust, Secure by Design y Shift Left no tenían evidencia propia; Shift Left no incluía análisis estático de código ni detección de secretos en el repositorio | RS-30…RS-32, M-16 | Matrices en `docs/cumplimiento-normativo.md`; CI con **CodeQL** y **gitleaks** (FND-7) |
| B-04 | Los **archivos** se guardaban sin cifrar en el volumen (el spec los dejaba fuera de alcance "salvo que lo pida el docente"), pero el docente pide proteger **toda** la información de las salas | RS-12, RS-13 | Cifrado por archivo con DEK propia envuelta con `kek_media_v{n}`: MED-1 (columnas y KEK), MED-3 (cifrar al guardar, descifrar al servir), MED-4 (liberar y rotar), FND-6 (secreto) |
| B-05 | El panel podía crear y desactivar salas, pero **no modificarlas** (la API sí) | RF-08 | Formulario *Editar* en FE-3 |
| B-06 | El cierre de sala aparecía como "Desactivar/eliminar", sin la semántica del enunciado | RF-09 | Spec §8.1 y §9.3 hablan de *cierre*; el botón es *Cerrar sala* (FE-3) |
| B-07 | Las alertas solo existían como filas de una tabla; el admin tenía que abrir la pestaña | RF-11, RS-20 | Insignia con el conteo de alertas nuevas en el panel (FE-5) |
| B-08 | No había un entregable que reuniera la evidencia de las pruebas | RP-05 | `docs/informe-pruebas.md` en E2E-3 (resultados por servicio, e2e y calibración) |
| B-09 | El vínculo "un dispositivo" por cookie no estaba declarado como límite | RS-05 | Limitación 7 en el spec §3 |
| B-10 | No había cuentas, roles ni JWT; el docente los pidió en la clase del 22/10 | RF-01, RF-17, RF-31, RF-32, RF-35, RS-01, RS-02, RS-05, RS-35, RS-36 | `auth` rev. 4: registro, RBAC con roles dinámicos, JWT RS256 con sesión revocable y una sesión por cuenta (ATH-1…ATH-4, GW-1) |
| B-11 | Solo el admin creaba y administraba salas | RF-03, RF-07, RF-13, RF-36 | Salas con dueño, máximo 2 por persona, membresía persistente y cesión (ROOM-2…ROOM-4) |
| B-12 | La única moderación era cerrar la sala entera, y no había suspensión de cuentas | RF-33, RF-34, RF-37…RF-39 | Expulsión con veto, silencio, borrado de mensajes, suspensión y cambio de contraseña (ROOM-4, CHAT-3, ATH-5) |
| B-13 | No había una API de esteganografía independiente ni los entregables del parcial | RF-40, RP-10, RP-11 | Servicio `stego` (STG-1…STG-4), colección de Postman e informe del parcial |
| B-14 | Nada impedía que un administrador leyera las conversaciones | RS-37, RF-08 | El admin global no lee mensajes ni cambia la clave de salas ajenas (spec §9.3, limitación 8) |

Quedan **fuera de alcance** (con su disparador en el spec §3): reportes, edición de mensajes, moderadores de sala, correo y recuperación de contraseña, notificaciones y estadísticas, formatos distintos de PNG/JPEG, mTLS entre servicios y varias réplicas.
