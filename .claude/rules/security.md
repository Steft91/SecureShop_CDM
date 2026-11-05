# Invariantes de seguridad (aplican a todo el repo)

Fuente: spec §2–§15 y Tabla 3 de la Tarea 2, recortados al primer parcial (gateway, auth y stego). Si un cambio rompe una de estas reglas, se detiene y se discute; no se "arregla después".

1. **Transporte:** el cliente solo habla TLS 1.3 con el gateway. Nunca `http://` hacia el cliente: el gateway redirige con 301.
2. **Secretos:** solo se leen con `shared.secrets` desde `/run/secrets`. Nunca en el código, en variables de entorno ni en logs. Los valores de prueba viven en `tests/` o en `shared/testing.py` y lo dicen en un comentario.
3. **Identidad:** el usuario sale de la identidad que verificó el gateway (`require_user`, `require_perm`, `user_from_headers`). Nunca del cuerpo de la petición.
4. **Autorización:** por permiso del catálogo (`require_perm`), siempre en el servidor. Nunca por el rol del JWT ni por un campo del cuerpo. Los modelos de entrada usan `extra="forbid"`.
5. **SQL:** siempre `text()` con parámetros nombrados. Prohibido interpolar datos con f-strings.
6. **Contraseñas:** Argon2id (`shared.passwords`), con verificación contra un hash dummy cuando el usuario no existe.
7. **Errores:** el cliente recibe `{"error": "..."}` genérico; el detalle va al registro de eventos. Todo rechazo de seguridad y todo acceso otorgado se registra con `shared.audit.emit(...)`.
8. **Datos sensibles:** nunca se registran contraseñas, tokens (JWT incluidos) ni secretos.
9. **Fallar cerrado:** si falta un secreto, el servicio no arranca. Si la BD no responde → 503. Si el análisis de una imagen falla o se pasa de tiempo, el resultado es `no_concluyente`, nunca `sin_indicios` (spec §23.7).
10. **Cripto:** solo con `shared.crypto` y PyJWT con `algorithms=["RS256"]` fijo. Nada de primitivas propias.
11. **Documentos de cumplimiento:** un cambio de control, algoritmo, clave o ruta de datos actualiza `docs/trazabilidad-riesgos.md` y, si aplica, `docs/justificacion-criptografica.md` y `docs/cumplimiento-normativo.md`.
