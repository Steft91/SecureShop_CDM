# Trazabilidad de riesgos → controles → pruebas

Fuente de riesgos: Tarea 2 (Tablas 1–4) + R16 (spec §16.3), recortada al primer parcial (gateway, auth y stego). Cada tarea del plan actualiza su fila. "Implementado" exige un test en verde.

La columna *ISO/IEC 27001:2022* relaciona cada control con el Anexo A; el detalle (mecanismo y evidencia) está en `docs/cumplimiento-normativo.md` §1.2. Los requisitos RF/RS del docente están en `docs/requisitos.md`.

| R | Riesgo | Control en el primer parcial | ISO/IEC 27001:2022 | Servicio / archivos | Tests | Estado |
|---|---|---|---|---|---|---|
| R2 | Claves criptográficas en el código fuente | Docker secrets (`/run/secrets`); la clave de firma del JWT nunca está en el código | A.8.24, A.8.9, A.8.12 | shared (`services/shared/shared/secrets.py`), auth | `services/shared/tests/test_r02_secretos.py` | En progreso (faltan `gen_secrets.py`, FND-6, y la clave de firma del JWT, ATH-1) |
| R4 | Fuerza bruta contra las cuentas | Bloqueo + retraso progresivo del login | A.8.5, A.5.17 | auth | — | Pendiente |
| R5 | Operaciones sin verificación de permisos | `auth_request` con permisos actuales + `require_perm` en cada servicio; el registro no asigna roles; nunca sin admin | A.5.15, A.8.2, A.5.18 | gateway, auth, stego | — | Pendiente |
| R6 | Imágenes con esteganografía | chi², RS y estructura (`stego`) con veredicto | A.8.7, A.8.16 | stego | — | Pendiente |
| R7 | Canal sin cifrar | TLS 1.3 en el gateway, http → https | A.8.20, A.8.24 | gateway | — | Pendiente |
| R9 | Archivos maliciosos | Magic bytes, Pillow, tope de tamaño y de píxeles (`stego`) | A.8.7, A.8.28 | stego | — | Pendiente |
| R10 | Agotamiento de recursos | Rate limit en Nginx + token bucket por usuario en `stego` + tope de registros por IP | A.8.6, A.8.20 | gateway, auth, stego | — | Pendiente |
| R11 | Credenciales de BD con privilegios excesivos | Rol `auth_app` sin DDL, BD propia de `auth` | A.8.2, A.5.18, A.8.22 | auth | — | Pendiente |
| R13 | Sesiones simultáneas de una cuenta | Índice único parcial en `user_sessions` + sesión ligada a la cookie de dispositivo + vencimiento por inactividad | A.5.16, A.5.15, A.8.5 | auth | — | Pendiente |
| R16 | Suplantación entre microservicios | Token por servicio con hash, allowlist, gateway sobrescribe identidad | A.5.15, A.8.21, A.8.22 | shared (`services/shared/shared/service_auth.py`, `identity.py`, `web.py`, `observability.py`), gateway, auth, stego | `services/shared/tests/test_r16_service_auth.py`, `test_observabilidad.py` | En progreso (falta e2e del gateway) |

Quedan fuera del primer parcial, hasta que el docente defina los siguientes entregables: R1, R3 (por ahora los eventos de seguridad son registros JSON, sin cadena de hashes), R8, R12, R14 y R15.

## Verificación manual (evidencia para el informe)
| Prueba | Comando | Resultado esperado | Fecha / resultado |
|---|---|---|---|
| TLS 1.2 rechazado | `curl --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake | — |
| http → https | `curl -I http://localhost/` | `301` | — |
| /internal no enrutado | `curl https://localhost/internal/verify` | `404` JSON | — |
| Cabeceras de identidad falsificadas | `curl -H "X-User-Id: x" -H "X-User-Perms: roles:manage" https://localhost/api/admin/roles` | `401` JSON | — |
| Flujo del parcial (Postman) | Runner de `docs/postman/parcial-1.postman_collection.json` | todas las pruebas en verde | — |
