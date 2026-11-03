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

## Estado

La colección se implementará cuando los contratos ejecutables de `auth` y gateway estén disponibles. Hasta entonces, las pruebas de Stego se validan mediante pytest, calibración y llamadas directas a su API.
