# Verificación manual del stack completo (2026-11-04)

Stack: `docker compose -f deploy/docker-compose.yml up -d --build` con `db`, `auth-migrate`, `auth`,
`stego-migrate`, `stego` y `gateway` (las dos migraciones salen con 0 y los servicios quedan `healthy`).
Admin creado con `python -m auth_svc.create_admin root --email root@example.com --password-stdin`.
Certificado: autofirmado temporal para `localhost` (curl con `-k`); en la demo se usa el de mkcert.

| Prueba | Comando | Resultado |
|---|---|---|
| http → https | `curl -I http://localhost/api/auth/profile` | `301` a `https://localhost/api/auth/profile` |
| TLS 1.2 rechazado | `curl -k --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake (curl sale con 35) |
| Cabeceras de seguridad | `curl -k -D - https://localhost/api/auth/profile` | `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Server: nginx` sin versión |
| `X-Request-ID` | mismo `curl` con `-H "X-Request-ID: inyectado"` | una sola cabecera, generada por el gateway (no la del cliente) |
| Identidad falsificada sin JWT | `curl -k -H "X-User-Id: x" -H "X-User-Perms: roles.manage" https://localhost/api/roles` | `401` |
| Permiso falsificado con JWT de USER | `POST /api/steganography/analyze` con `X-User-Perms: steganography.analyze` | `403`: el gateway sobrescribe la cabecera con lo que decide `auth` |
| `/internal` no expuesto | `curl -k -X POST https://localhost/internal/authorization/check` | `404` |
| T01: `stego` detenido | `docker compose stop stego` y analizar; luego `GET /api/auth/profile` | `503` en el análisis; `auth` responde `200` |
| T08: `auth` detenido | `docker compose stop auth` y la carpeta 3 de la colección | `503`; ninguna petición llega a `stego` |
| T12: eventos | `docker compose logs gateway auth stego` → `eventos-demo.log` | 331 líneas, todas las de `auth` y `stego` con `request_id`; 0 JWT (`eyJ`), 0 `Bearer`, 0 contraseñas |
| Colección (T02–T07, T09–T11) | `npx newman run docs/postman/parcial-1.postman_collection.json` (carpetas 1 y 2) | 36 peticiones, 57 aserciones, 0 fallas (`postman-newman.txt`); repetible sin limpiar la BD |
