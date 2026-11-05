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

### Instalación en Windows

Abre PowerShell como administrador para instalar las herramientas del sistema. Si
Chocolatey aún no está instalado, sigue primero su [guía oficial de
instalación](https://chocolatey.org/install). Después instala `mkcert`:

```powershell
choco install mkcert -y
```

Cierra y vuelve a abrir VS Code o PowerShell para que se actualice el `PATH`.
`mkcert -install` instala la CA local en Windows y, si existe un JDK instalado,
también en el almacén de certificados de Java; por eso este comando debe
ejecutarse desde una terminal como administrador:

```powershell
mkcert -install
```

## Puesta en marcha

```bash
git clone https://github.com/Steft91/SecureShop_CDM.git
cd SecureShop_CDM
```

1. **Entorno de Python.** Va primero porque `gen_secrets.py` usa `cryptography`, y `stego_lab.py` (sección de Postman) usa `numpy` y `Pillow`:

   ```bash
   py -3.13 -m venv .venv                      # macOS/Linux: python3.13 -m venv .venv
   .venv\Scripts\activate                      # macOS/Linux: source .venv/bin/activate
   pip install -e "services/shared[dev]" -e services/auth -e services/stego
   ```

2. **Secretos.** Crea las contraseñas de las BD, la clave de firma del JWT y el token del gateway en `deploy/secrets/`. Esa carpeta no se versiona, y el script solo genera los secretos que faltan.

   ```bash
   python deploy/gen_secrets.py
   ```

3. **Certificado TLS.** Instala la CA local de mkcert una vez y crea el certificado para `localhost`:

   ```powershell
   New-Item -ItemType Directory -Force deploy\certs
   mkcert -install
   mkcert -cert-file deploy\certs\fullchain.pem `
          -key-file deploy\certs\privkey.pem `
          localhost 127.0.0.1 ::1
   ```

4. **Levantar el stack.** Arranca `db`, `auth-migrate`, `auth`, `stego-migrate`, `stego` y `gateway`:

   ```powershell
   docker compose -f deploy/docker-compose.yml up -d --build --wait
   ```

   `auth-migrate` y `stego-migrate` aplican las migraciones y se apagan. Que aparezcan como `Exited (0)` en `docker compose -f deploy/docker-compose.yml ps -a` es lo esperado: `auth` y `stego` solo arrancan cuando su migración termina bien. Si el código no es 0, la causa está en `docker compose -f deploy/docker-compose.yml logs auth-migrate stego-migrate`.

   El archivo Compose está dentro de `deploy`; si prefieres trabajar desde esa carpeta, usa:

   ```powershell
   cd deploy
   docker compose up -d --build --wait
   ```

   Desde la raíz, todo `docker compose` (también `logs` y `ps`) necesita `-f deploy/docker-compose.yml`; sin él, Compose no encuentra ningún archivo de configuración.

   Si ya tenías el volumen `pgdata` de una versión anterior (por ejemplo, sin la BD de `stego`), recréalo con `down -v`; esto borra los datos locales y vuelve a ejecutar las migraciones:

   ```powershell
   docker compose -f deploy/docker-compose.yml down -v
   docker compose -f deploy/docker-compose.yml up -d --build --wait
   ```

   Para comprobar el gateway y TLS (no hay `/health` público, y las rutas internas no se exponen):

   ```bash
   curl -i https://localhost/internal/authorization/check   # Windows: curl.exe -i --ssl-no-revoke https://localhost/internal/authorization/check
   ```

   Debe responder `404` con `{"error":"no encontrado"}`. En Windows, curl necesita `--ssl-no-revoke` porque la CA de mkcert no publica una lista de revocación; la cadena del certificado se sigue verificando, a diferencia de `-k`.

5. **Crear el administrador.** No existen credenciales por defecto. El CLI pide la contraseña dos veces, sin mostrarla; en scripts, `exec -T` con `--password-stdin` la lee de la entrada estándar:

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
2. Crea un entorno con `admin_username` y `admin_password`, las del administrador del paso 5, y selecciónalo arriba a la derecha.
3. En *Settings → General*, apunta el *Working directory* a la raíz del repositorio (las imágenes salen de `docs/demo-imagenes/`) y deja activado *SSL certificate verification*.
4. En *Settings → Certificates*, activa **CA certificates** y, en *PEM file*, elige `rootCA.pem` de la carpeta que imprime `mkcert -CAROOT` (en Windows, `%LOCALAPPDATA%\mkcert`). No uses *Add certificate*, que es para certificados de cliente, y nunca cargues `rootCA-key.pem`: es la clave privada de la CA.
5. Genera el archivo de más de 5 MB, que no se versiona: `python services/stego/tools/stego_lab.py demo docs/demo-imagenes`. Qué es cada imagen y qué resultado se espera: `docs/calibracion-estego.md`, sección *Imágenes de la demo*.
6. Runner: sobre la colección, *⋯ → Run collection*. Desmarca la carpeta `3`, deja *Iterations* en 1 y, en *Advanced settings*, *Keep variable values* activado (si corres las carpetas por separado, la `2` usa el usuario y los tokens que guardó la `1`). Se puede repetir: los usuarios de prueba llevan un sufijo distinto en cada corrida.
7. Carpeta `3` (T08): `docker compose -f deploy/docker-compose.yml stop auth`, *⋯ → Run folder* sobre ella y, al terminar, `docker compose -f deploy/docker-compose.yml start auth`.

Por consola:

```bash
npx newman run docs/postman/parcial-1.postman_collection.json -e <entorno>.json --folder "1 - Admin" --folder "2 - Usuario y Stego" --working-dir .
```

## Escenarios de la demo (Anexo D)

| ID | Cómo |
|---|---|
| T01 | `docker compose -f deploy/docker-compose.yml stop stego`: el análisis da 503 y `auth` sigue respondiendo. Lo mismo al revés con `auth`. Después, `start stego` (o `start auth`) |
| T02–T07, T09–T11 | Colección de Postman, carpetas 1 y 2 |
| T08 | `docker compose -f deploy/docker-compose.yml stop auth` y la carpeta 3: 503, y ningún `stego.analyzed` en los registros. Después, `start auth` |
| T12 | `docker compose -f deploy/docker-compose.yml logs gateway auth stego`: eventos JSON con `request_id`, sin JWT ni contraseñas |

`zip-al-final.png` se ve como una imagen normal, pero lleva un ZIP pegado. Para mostrar el archivo oculto:

```bash
python -I -c "import zipfile; print(zipfile.ZipFile('docs/demo-imagenes/zip-al-final.png').read('mensaje.txt').decode())"
```

La evidencia de una corrida completa está en `docs/evidencias/`.

## Pruebas

Con el entorno del paso 1 activo:

```bash
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
