# Salas de Chat Seguras: Backend V1 (primer parcial)

Dos microservicios REST detrás de un API Gateway:

- **`auth`** administra usuarios, roles (ADMIN, ANALYST, USER) y su relación N:M `user_roles`. Emite JWT firmados con RS256 y decide la autorización vigente en cada petición.
- **`stego`** valida y analiza imágenes en busca de esteganografía (chi², RS y entropía del LSB, más la estructura del archivo). Clasifica cada archivo en `sin_indicios`, `sospechoso`, `no_concluyente` o `error`, aplica una política y guarda cada análisis.

El gateway (Nginx) es el único punto de entrada. Termina TLS 1.3, aplica rate limit y, en cada petición, pregunta a `auth` (`POST /internal/authorization/check`) antes de enrutar.

Equipo: Zaith Manangón, Andrés Cedeño y Stefany Díaz. Enunciado: `docs/enunciado/`.

## Requisitos

- Docker con Docker Compose v2
- Python 3.13, para generar los secretos y correr las pruebas
- [mkcert](https://github.com/FiloSottile/mkcert), para el certificado TLS local
- Postman, o Node.js para correr la colección con `npx newman`

## Puesta en marcha

```bash
git clone https://github.com/Steft91/SecureShop_CDM.git
cd SecureShop_CDM
```

1. **Secretos.** Crea las contraseñas de las BD, la clave de firma del JWT y el token del gateway en `deploy/secrets/`. Esa carpeta no se versiona, y el script solo genera los secretos que faltan.

   ```bash
   python deploy/gen_secrets.py
   ```

2. **Certificado TLS.** Instala la CA local de mkcert una vez y crea el certificado para `localhost`:

   ```bash
   mkcert -install
   mkcert -cert-file deploy/certs/fullchain.pem -key-file deploy/certs/privkey.pem localhost 127.0.0.1 ::1
   ```

3. **Levantar el stack.** Arranca `db`, `auth-migrate`, `auth`, `stego-migrate`, `stego` y `gateway`:

   ```bash
   docker compose -f deploy/docker-compose.yml up -d --build --wait
   ```

   Si ya tenías el volumen `pgdata` de una versión sin la BD de `stego`, recréalo con `docker compose -f deploy/docker-compose.yml down -v`. Ojo: eso borra los datos locales.

4. **Crear el administrador.** No existen credenciales por defecto. El CLI pide la contraseña dos veces, sin mostrarla; en scripts, `exec -T` con `--password-stdin` la lee de la entrada estándar:

   ```bash
   docker compose -f deploy/docker-compose.yml exec auth python -m auth_svc.create_admin <usuario> --email <correo>
   ```

Cada servicio tiene su `.env.example` (`services/auth/.env.example` y `services/stego/.env.example`), solo con variables no secretas. Los secretos se leen siempre desde `/run/secrets`.

## API

| Servicio | Método | Ruta | Acceso |
|---|---|---|---|
| AUTH | POST | `/api/auth/login` | Público, con límite de intentos |
| AUTH | GET | `/api/auth/profile` | Usuario autenticado |
| AUTH | POST | `/api/auth/logout` | Sesión autenticada |
| AUTH | POST, GET | `/api/users` | ADMIN (`users.manage`) |
| AUTH | PATCH | `/api/users/{id}` | ADMIN (`users.manage`) |
| AUTH | GET | `/api/roles/permissions` | ADMIN (`roles.manage`) |
| AUTH | POST, GET | `/api/roles` | ADMIN (`roles.manage`) |
| AUTH | PATCH | `/api/roles/{id}` | ADMIN (`roles.manage`) |
| AUTH | POST | `/api/user-roles` | ADMIN (`roles.manage`) |
| AUTH | DELETE | `/api/user-roles/{id}` | ADMIN (`roles.manage`) |
| AUTH | POST | `/internal/authorization/check` | Solo el gateway, con token de servicio; desde afuera da 404 |
| STEGO | POST | `/api/steganography/analyze` | ADMIN o ANALYST (`steganography.analyze`) |
| STEGO | GET | `/api/steganography/results/{id}` | El dueño, o quien tenga `steganography.results.read_any` |

Las especificaciones OpenAPI están en `docs/openapi/auth.json` y `docs/openapi/stego.json`.

## Colección de Postman

1. Importa `docs/postman/parcial-1.postman_collection.json`.
2. Crea un entorno con `admin_username` y `admin_password`, las del administrador del paso 4.
3. En *Settings → General*, apunta el *Working directory* a la raíz del repositorio; las imágenes salen de `docs/demo-imagenes/`. En *Settings → Certificates*, agrega la CA de mkcert (`mkcert -CAROOT`).
4. Genera el archivo de más de 5 MB, que no se versiona: `python services/stego/tools/stego_lab.py demo docs/demo-imagenes`.
5. Ejecuta con el Runner las carpetas `1 - Admin` y `2 - Usuario y Stego`, en orden. La carpeta `3` se corre después de `docker compose -f deploy/docker-compose.yml stop auth`.

Por consola:

```bash
npx newman run docs/postman/parcial-1.postman_collection.json -e <entorno>.json --folder "1 - Admin" --folder "2 - Usuario y Stego" --working-dir .
```

## Escenarios de la demo (Anexo D)

| ID | Cómo |
|---|---|
| T01 | `docker compose -f deploy/docker-compose.yml stop stego`: el análisis da 503 y `auth` sigue respondiendo. Lo mismo al revés con `auth` |
| T02–T07, T09–T11 | Colección de Postman, carpetas 1 y 2 |
| T08 | `docker compose -f deploy/docker-compose.yml stop auth` y la carpeta 3: 503, y ningún `stego.analyzed` en los registros |
| T12 | `docker compose -f deploy/docker-compose.yml logs gateway auth stego`: eventos JSON con `request_id`, sin JWT ni contraseñas |

La evidencia de una corrida completa está en `docs/evidencias/`.

## Pruebas

```bash
py -3.13 -m venv .venv                      # macOS/Linux: python3.13 -m venv .venv
.venv\Scripts\activate                      # macOS/Linux: source .venv/bin/activate
pip install -e "services/shared[dev]" -e services/auth -e services/stego
docker compose -f deploy/docker-compose.test.yml up -d   # PostgreSQL de pruebas en 127.0.0.1:5433
pytest services/shared services/auth services/stego
ruff check services deploy && ruff format --check services deploy
```

La CI (`.github/workflows/ci.yml`) corre en cada push ruff, pytest con cobertura mínima del 80 %, bandit, pip-audit, CodeQL y gitleaks.

## Documentación

| Documento | Contenido |
|---|---|
| `docs/specs/2026-10-12-chat-seguro-design.md` (§23) | Diseño del primer parcial |
| `docs/trazabilidad-riesgos.md` | Riesgos, controles, pruebas y verificación manual |
| `docs/requisitos.md` | Requisitos del docente y cómo se cumplen |
| `docs/cumplimiento-normativo.md` | ISO/IEC 27001 y 27034, Zero Trust, Secure by Design y Shift Left |
| `docs/justificacion-criptografica.md` | Algoritmos y claves |
| `docs/calibracion-estego.md` | Técnica, parámetros, calibración y limitaciones del estegoanálisis |
