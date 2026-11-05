# Colección de Postman del primer parcial

Este directorio está reservado para `PAR-1`, a cargo de Stefany.

## Alcance

La colección recorrerá el flujo del primer parcial:

1. Registro de un usuario sin privilegios.
2. Rechazo de asignación masiva de rol.
3. Login y consulta de identidad.
4. Rechazo de Stego sin token y sin permiso.
5. Login del administrador.
6. Creación y asignación del rol `stego:analyze`.
7. Análisis de las cuatro imágenes de demostración.
8. Verificación de que los permisos actualizados aplican en la siguiente petición.
9. Casos negativos y evidencias de logs.

## Variables

La colección no debe contener secretos reales. Los valores sensibles se guardan únicamente como variables locales de Postman:

- `base_url`: `https://localhost`.
- `admin_username`: variable local.
- `admin_password`: variable local.
- `username`, `user_id`, `user_token`, `admin_token`, `role_id`: variables generadas durante la ejecución.

## Requisitos para ejecutar

- Gateway, `auth` y `stego` levantados.
- Certificado local de `mkcert` confiable en Postman.
- Verificación SSL activada.
- Directorio de trabajo de Postman ubicado en la raíz del repositorio.
- Las imágenes de demo generadas localmente en `docs/demo-imagenes/`.

## Colección disponible

La colección `parcial-1.postman_collection.json` contiene el flujo integrado actual:

- Login del administrador.
- Consulta del catálogo de permisos.
- Creación de usuario y rol analista.
- Asignación del permiso `steganography.analyze`.
- Listado y actualización de usuarios y roles con autorización `ADMIN`.
- Login y perfil del usuario.
- Análisis de las cuatro imágenes demo.
- Cierre de sesión autenticado.

Las rutas usan el contrato real del gateway: `/api/steganography/analyze`, `/api/users`, `/api/roles` y `/api/user-roles`.

## Cobertura del contrato mínimo

La colección cubre las rutas ejecutables del contrato mínimo:

- AUTH: login, profile, logout, usuarios (POST/GET/PATCH), roles (POST/GET/PATCH) y user-roles (POST).
- STEGO: POST `/api/steganography/analyze`, con casos limpia, problema, revisión manual y archivo inválido (422).

La ruta GET `/api/steganography/results/:id` queda documentada como pendiente: el gateway reconoce su permiso, pero el servicio Stego actual no persiste ni expone resultados consultables. No se agrega una prueba falsa que aparente cubrirla.

## Orden de ejecución

Ejecuta la carpeta `1 - Admin` completa y luego `2 - Usuario y Stego` en orden. `Cerrar sesión usuario` debe ser la última solicitud porque invalida `user_token`. Si vuelves a ejecutar la colección, usa un `demo_user` y `demo_email` nuevos o elimina previamente el usuario creado.
