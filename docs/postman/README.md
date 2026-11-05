# Colección de Postman del primer parcial

`parcial-1.postman_collection.json` contiene 37 peticiones y recorre por el gateway el contrato mínimo del enunciado (§2.5) y los escenarios T02–T11 del Anexo D. No contiene secretos: las credenciales del administrador van en un entorno local, y los usuarios de prueba se crean con un sufijo distinto en cada corrida, así que se puede repetir sin limpiar la BD.

## Cómo ejecutarla

1. Stack levantado y administrador creado (ver `README.md` de la raíz).
2. Entorno de Postman con `admin_username` y `admin_password`.
3. *Working directory* en la raíz del repositorio y la CA de mkcert (`rootCA.pem`) en *Settings → Certificates → CA certificates*; el detalle está en el `README.md` de la raíz.
4. `python services/stego/tools/stego_lab.py demo docs/demo-imagenes` para generar `grande.png`, que no se versiona.
5. Runner: carpetas `1 - Admin` y `2 - Usuario y Stego`, en orden.
6. Carpeta `3 - Manual: AUTH detenido (T08)`: solo después de `docker compose -f deploy/docker-compose.yml stop auth`. Luego, `docker compose -f deploy/docker-compose.yml start auth`.

La colección valida el JWT ausente y manipulado. El caso de JWT vencido se verifica en `services/auth/tests/test_r16_check.py::test_jwt_vencido_401`; no se duplica en la colección porque su expiración no es reproducible de forma segura en Newman.

## Cobertura

| Ruta del enunciado | Petición |
|---|---|
| `POST /api/auth/login` | Login admin, Login con contraseña inválida, logins de los usuarios de prueba |
| `GET /api/auth/profile` | Perfil usuario, Perfil con la sesión cerrada |
| `POST /api/auth/logout` | Cerrar sesión |
| `POST` y `GET /api/users` | Crear usuario demo y los otros dos; Listar usuarios |
| `PATCH /api/users/:id` | Actualizar usuario |
| `POST` y `GET /api/roles` | Crear rol analista, Listar roles (más `GET /api/roles/permissions`) |
| `PATCH /api/roles/:id` | Actualizar rol |
| `POST /api/user-roles` | Las cuatro asignaciones y la repetida (409) |
| `DELETE /api/user-roles/:id` | Retirar el rol analista al usuario demo |
| `POST /internal/authorization/check` | Lo llama el gateway en cada petición protegida; "Ruta interna no expuesta" comprueba el 404 desde afuera |
| `POST /api/steganography/analyze` | Referencia, LSB, ZIP al final, no es imagen (415), truncada (422), más de 5 MB (413) y los rechazos 401 y 403 |
| `GET /api/steganography/results/:id` | Consultar resultado propio (200) y análisis ajeno (403) |

| Escenario | Petición | Esperado |
|---|---|---|
| T02 | Login admin / Login con contraseña inválida | 200 con JWT / 401 |
| T03 | Analizar sin token / con JWT manipulado | 401 |
| T04 | USER intenta analizar | 403 |
| T05 | Asignar dos roles al usuario demo y el rol analista a dos usuarios; Listar usuarios | 201 y dos roles en el listado |
| T06 | Repetir una asignación | 409 |
| T07 | Retirar el rol y analizar con el mismo JWT | 204 / 403 |
| T08 | Carpeta 3 con `auth` detenido | 503 |
| T09 | Referencia / LSB | `sin_indicios` / `sospechoso` con indicadores y limitaciones |
| T10 | No es imagen / truncada / más de 5 MB | 415 / 422 / 413 |
| T11 | Consultar análisis ajeno | 403 |

T01 y T12 se demuestran con `docker compose` (ver `README.md`). La salida de una corrida completa está en `docs/evidencias/postman-newman.txt`; la captura del Runner se incorpora como evidencia de la sustentación.
