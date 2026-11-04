# Modelo de confianza entre microservicios (R16, spec §4.3)

- El gateway es el único punto de entrada y el único que habla con `auth` y `stego`. Los servicios no se llaman entre sí.
- Toda ruta de un servicio exige `X-Service-Token` válido (`ServiceTokenMiddleware`, que agrega `shared.web.create_base_app`). Solo `/health` está exento.
- Rutas públicas (enrutadas por el gateway): `Depends(require_gateway)`, `Depends(require_user)` o `Depends(require_perm("<permiso>"))`. Rutas internas: `/internal/...` con `Depends(allow("<llamador>", ...))`.
- Las cabeceras `X-User-Id`, `X-User-Name`, `X-Session-Id` y `X-User-Perms` **solo** se leen a través de `shared.identity`, que exige que el llamador sea `gateway`. Los permisos que traen son los actuales: el gateway los pide a `auth` en cada request.
- Un servicio con datos se conecta **solo a su BD** con su rol `<svc>_app`. En el primer parcial solo `auth` tiene BD; `stego` no guarda nada.
- Allowlist vigente: auth ← gateway · stego ← gateway.
- Agregar un servicio o un llamador requiere tocar:
  - la red en `deploy/docker-compose.yml`;
  - los secretos `svc_token_*`/`svc_hash_*` y `deploy/gen_secrets.py`;
  - el rol de BD en `deploy/postgres/init.sh` (si el servicio guarda datos);
  - la allowlist del receptor;
  - esta regla.
