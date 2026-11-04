# Trazabilidad de riesgos → controles → pruebas

Fuente de riesgos: Tarea 2 (Tablas 1–4) + R16 (spec §16.3), recortada al primer parcial (gateway, auth y stego). Cada tarea del plan actualiza su fila. "Implementado" exige un test en verde.

La columna *ISO/IEC 27001:2022* relaciona cada control con el Anexo A; el detalle (mecanismo y evidencia) está en `docs/cumplimiento-normativo.md` §1.2. Los requisitos RF/RS del docente están en `docs/requisitos.md`.

| R | Riesgo | Control en el primer parcial | ISO/IEC 27001:2022 | Servicio / archivos | Tests | Estado |
|---|---|---|---|---|---|---|
| R2 | Claves criptográficas en el código fuente | Docker secrets (`/run/secrets`); la clave de firma del JWT nunca está en el código | A.8.24, A.8.9, A.8.12 | shared (`services/shared/shared/secrets.py`), deploy (`deploy/gen_secrets.py`), auth | `services/shared/tests/test_r02_secretos.py`, `test_gen_secrets.py` | En progreso (falta que auth cargue la clave de firma del JWT, ATH-1) |
| R4 | Fuerza bruta contra las cuentas | Bloqueo + retraso progresivo del login | A.8.5, A.5.17 | auth | — | Pendiente |
| R5 | Operaciones sin verificación de permisos | `auth_request` a `POST /internal/authorization/check`, que decide por acción con los roles activos de la BD (spec §23.6) + `require_perm` en cada servicio; propiedad del análisis en `stego` (T11); la cuenta nace sin roles; nunca sin ADMIN | A.5.15, A.8.2, A.5.18 | gateway, auth, stego | — | Pendiente (ATH-2, ATH-4, STG-3) |
| R6 | Imágenes con esteganografía | chi², RS y estructura (`stego`) → `sin_indicios`/`sospechoso`/`no_concluyente`/`error` con política y registro persistido (spec §23.7) | A.8.7, A.8.16 | stego | — | Pendiente (código en `feat/stefany-stego`, sin integrar) |
| R7 | Canal sin cifrar | TLS 1.3 en el gateway, http → https | A.8.20, A.8.24 | gateway | — | Pendiente |
| R9 | Archivos maliciosos | Extensión, `Content-Type` y magic bytes (415), Pillow, tope de tamaño (413) y de píxeles (422); el archivo sospechoso queda en un volumen sin ruta y los demás se descartan (`stego`) | A.8.7, A.8.28 | stego | — | Pendiente (STG-2, STG-3) |
| R10 | Agotamiento de recursos | Rate limit en Nginx + bloqueo del login + token bucket por usuario en `stego` + tope de 5 MB (sin registro abierto, ya no hace falta el tope por IP) | A.8.6, A.8.20 | gateway, auth, stego | — | Pendiente |
| R11 | Credenciales de BD con privilegios excesivos | Roles `auth_app` y `stego_app` sin DDL, una BD por servicio; `stego_app` solo `SELECT`/`INSERT` (spec §23.7) | A.8.2, A.5.18, A.8.22 | deploy (`deploy/postgres/init.sh`: BD `auth` y `stego`, cada una con `<svc>_owner`/`<svc>_app`, sin acceso a `postgres` ni `template1`; `deploy/gen_secrets.py`: `db_stego_*`; compose: `stego-migrate` con el rol owner y `stego` con el rol app), auth, stego | `services/shared/tests/test_testing.py` (`assert_least_privilege`) | En progreso (falta `test_r11_*` de auth y de stego, ATH-1 y STG-3; BD `stego` en `init.sh`, GW-1) |
| R13 | Sesiones simultáneas de una cuenta | Fuera del primer parcial: el enunciado excluye la restricción de dispositivos (spec §23.1). Mientras tanto, cada sesión se revoca con logout o al desactivar la cuenta, y el JWT vence a los 15 min | A.5.16, A.5.15, A.8.5 | auth | — | Fuera del parcial |
| R16 | Suplantación entre microservicios | Token por servicio con hash, allowlist, gateway sobrescribe identidad | A.5.15, A.8.21, A.8.22 | shared (`services/shared/shared/service_auth.py`, `identity.py`, `web.py`, `observability.py`), deploy (`deploy/gen_secrets.py`: token del gateway y su hash; red `apps` interna; `FORWARDED_ALLOW_IPS` en `services/Dockerfile`), gateway (`gateway/snippets/*.conf`: identidad, `Authorization` y cookies vaciadas hacia los servicios), auth, stego | `services/shared/tests/test_r16_service_auth.py` (incluye `test_csrf_rechaza_origin_ajeno` y `test_sin_origin_pasa_porque_no_hay_cookies`), `test_observabilidad.py` | En progreso (falta e2e del gateway; `stego` de `feat/stefany-stego` todavía no usa `shared`) |

Quedan fuera del primer parcial, hasta que el docente defina los siguientes entregables: R1, R3 (por ahora los eventos de seguridad son registros JSON, sin cadena de hashes), R8, R12, R14 y R15.

## Verificación manual (evidencia para el informe)
| Prueba | Comando | Resultado esperado | Fecha / resultado |
|---|---|---|---|
| TLS 1.2 rechazado | `curl --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake | — |
| http → https | `curl -I http://localhost/` | `301` | — |
| /internal no enrutado | `curl -X POST https://localhost/internal/authorization/check` | `404` JSON | — |
| Cabeceras de identidad falsificadas | `curl -H "X-User-Id: x" -H "X-User-Perms: roles.manage" https://localhost/api/roles` | `401` JSON | — |
| AUTH caído (T08) | `docker compose stop auth` y analizar con un JWT válido | `503` y ningún `stego.analyzed` | — |
| Flujo del parcial (Postman, T01–T12) | Runner de `docs/postman/parcial-1.postman_collection.json` | todas las pruebas en verde | — |
