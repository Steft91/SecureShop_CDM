# Actividad de Aprendizaje: Reconocimiento de activo

| **Departamento:** | Ciencias de la Computación | **Carrera:** | Software |
|---|---|---|---|
| **Asignatura:** | Software Seguro | **Nivel:** | 7mo |
| **Docente:** | Ing. Ángel Cudco | **Tarea N°:** | 1 |
| **Fecha:** | 29/09/2026 | **Calificación:** | |

**Integrantes:**

- Zaith Alejandro Manangón Vinueza
- Stefany Maricela Díaz Antun
- Andrés Isaias Cedeño Cuenca

---

## Antecedentes

### Arquitectura de Microservicios - SecureShop

```mermaid
flowchart LR
    C["Cliente / Usuario<br/>Consume el sistema SecureShop"] -->|"Solicitudes HTTP (API REST)"| G["API Gateway<br/>Punto de entrada a los microservicios"]
    G --> U["User Service<br/>• Registrar usuarios<br/>• Consultar usuarios<br/>• Listar usuarios"]
    G --> P["Product Service<br/>• Registrar productos<br/>• Consultar productos<br/>• Listar productos<br/>• Actualizar productos"]
    G --> O["Order Service<br/>• Crear pedidos<br/>• Consultar pedidos<br/>• Listar pedidos"]
```

**SecureShop** es una empresa *ficticia* dedicada a la comercialización de productos tecnológicos a través de Internet. Debido al crecimiento de sus operaciones, requiere desarrollar una nueva plataforma web que permita administrar usuarios, productos y pedidos.

La empresa ha decidido construir la solución utilizando una arquitectura basada en microservicios, debido a que desea que sus componentes puedan desarrollarse, desplegarse y evolucionar independientemente.

El equipo de desarrollo deberá construir progresivamente una primera versión de la aplicación SecureShop, compuesta por servicios independientes para la administración de usuarios, productos y pedidos, una base de datos para cada dominio y un punto de entrada común para las solicitudes de los clientes.

Paralelamente al desarrollo funcional, el equipo deberá analizar los aspectos de seguridad que aparecen durante el ciclo de vida del software, identificando activos, vulnerabilidades potenciales, amenazas, riesgos, propiedades de seguridad, puntos de exposición y dependencias entre los diferentes componentes.

---

## Desarrollo

### Actividad 1

1. Crear un repositorio de GitHub.
2. Identificar al menos diez activos de SecureShop. Por ejemplo:
   - Información de usuarios
   - Credenciales
   - Catálogo de productos
3. Clasificar cada activo según:
   - información;
   - software;
   - servicio;
   - infraestructura;
   - datos.
4. Responder: ¿Qué consecuencias tendría para SecureShop que este activo fuera accedido, modificado o quedara indisponible?

| N. | Activo | Tipo | Consecuencia de acceso, modificación o indisponibilidad |
|---|---|---|---|
| 1 | Información de un Pedido | Información | Se expone el historial de compras y las direcciones de clientes; se pueden alterar los mismos (montos, cantidades, destino), lo que deriva en fraude y pérdidas económicas. |
| 2 | Logs y registros de auditoría | Datos | Pueden filtrar tokens, IPs o datos personales si se registran de más; con un atacante se puede perder evidencia forense. |
| 3 | API Gateway | Servicio | Es el punto de entrada único: un fallo de control permite llegar a todos los microservicios. Si quedara fuera de servicio, toda la plataforma queda caída. |
| 4 | Microservicios | Servicio | Con operaciones sin autenticación, funciones como "listar usuarios" quedan expuestas a cualquiera. Si llega a ser modificado, la lógica de negocio se altera. Si queda indisponible, se pierde la función de ese dominio (ej.: sin Product Service no se pueden completar ni crear los pedidos). |
| 5 | Base de datos de productos | Datos | Se expone el inventario y el catálogo completo; puede haber registros corruptos o productos a precios incorrectos; Product Service no responde. |
| 6 | Variables de entorno | Información sensible | Acceso directo a la base de datos con la posibilidad de generar montos y perfiles falsos. |
| 7 | Respaldos | Datos | Filtración masiva, ya que es una copia completa de todo; se podría restaurar un backup modificado con datos corruptos. |
| 8 | Red y canales de comunicación | Infraestructura | Intercepción de tráfico sobre HTTP, peticiones y respuestas alteradas en tránsito. Los servicios no logran comunicarse entre sí. |
| 9 | Base de datos de usuarios | Datos | Si se accediera a los datos, existiría filtración de todo el padrón de clientes junto con los hashes. Si se modificara, quedarían registros corruptos o cuentas inyectadas. Si quedara indisponible, el User Service caería junto con el login y el registro. |
| 10 | Código fuente (repositorio GitHub) | Software | Con el acceso al software se revelaría la lógica y las posibles vulnerabilidades. Si existen modificaciones, podría haber inyección de backdoors o código malicioso en el despliegue. Al quedar indisponible no se podría corregir, desplegar ni evolucionar el sistema. |
| 11 | Servidores / contenedores / nube donde se despliega | Infraestructura | Si se accede como root sin autorización se podría perder el control de todos los servicios y BD. Si se modificara la infraestructura, su configuración quedaría alterada con malware o minería de criptomonedas. Al quedar indisponible habría caída total del sistema. |
| 12 | Credenciales (contraseñas hasheadas, tokens de sesión/JWT) | Información | Al acceder a la información existiría suplantación de identidad, secuestro de cuentas y compras fraudulentas. Al haber modificación, alguien podría tomar el control de cuentas o escalar privilegios (volverse admin). Al quedar indisponible, nadie podría iniciar sesión y el sistema quedaría inutilizable. |
| 13 | Base de datos de pedidos | | |
| 14 | Servicio de pedidos (Order Service) | Software / Servicio | Si se accediera sin autorización al Order Service, un atacante podría consultar o manipular pedidos de otros clientes. Si se modificara su lógica, podría alterar el proceso de compra, por ejemplo, permitiendo crear pedidos sin realizar correctamente las validaciones. Si quedara indisponible, los clientes no podrían realizar ni consultar sus pedidos. |
| 15 | Información de pagos e integración con la pasarela de pagos | Información sensible | Si es accedida, se puede usar esa información para hacer fraude masivo; si queda indisponible no se podría cobrar y los pedidos quedarían sin pagar. |

---

## Actividad en clase

Añadir activos hasta sumar 15, a cada activo identificar 3 amenazas y a cada amenaza al menos un mecanismo de mitigación.

| N. | Activo | Amenaza | Mitigación |
|---|---|---|---|
| 1 | Información de un Pedido | 1. Un usuario consulta pedidos de otros cambiando el ID en la URL.<br>2. Manipulación de montos, cantidades o destino antes de confirmar el pedido.<br>3. Exposición de datos personales en respuestas o errores. | 1. Validar en cada petición que el pedido pertenezca al usuario autenticado.<br>2. Recalcular precios y totales en el servidor, no usar valores enviados por el cliente.<br>3. Devolver solo los campos necesarios (DTOs) y cifrar datos sensibles en reposo. |
| 2 | Logs y registros de auditoría | 1. Datos sensibles escritos en los logs.<br>2. Registro insuficiente de eventos de seguridad.<br>3. Borrado o alteración de logs por un atacante. | 1. Enmascarar o redactar campos sensibles en el logger y definir una política de qué se registra y qué no.<br>2. Definir los eventos de seguridad que se deben registrar, un correlation ID generado en el gateway y alertas para eventos críticos.<br>3. Centralizar los logs en un servidor separado (ELK, Loki), almacenamiento de solo escritura y una alerta si un servicio deja de enviar logs. |
| 3 | API Gateway | 1. Ataque de denegación de servicio (DDoS).<br>2. Bypass del gateway (acceso directo a los microservicios).<br>3. Configuración incorrecta de CORS o de rutas. | 1. Rate limiting, CDN/WAF con protección anti-DDoS (por ejemplo, Cloudflare), varias instancias del gateway y autoescalado.<br>2. Microservicios solo en la red interna (únicamente el gateway expuesto) y validación del token también en cada servicio (zero trust).<br>3. Lista blanca de orígenes permitidos, revisión de las rutas expuestas y política de denegar por defecto. |
| 4 | Microservicios (User / Product / Order) | 1. Endpoints sin autenticación o autorización.<br>2. Fallo en cascada entre servicios.<br>3. Suplantación de un servicio interno. | 1. Guards de autenticación y roles en cada endpoint (AuthGuard + RolesGuard en NestJS) con política de denegar por defecto.<br>2. Timeouts, reintentos con backoff, circuit breaker y health checks para retirar las instancias que fallan.<br>3. TLS entre servicios, propagación del JWT firmado en lugar de encabezados simples y validación en cada servicio. |
| 5 | Base de datos de productos | 1. Borrado o corrupción del catálogo.<br>2. Inconsistencia de stock por condiciones de carrera.<br>3. Denegación de servicio por consultas costosas. | 1. Consultas parametrizadas, borrado lógico (soft delete), backups automáticos con recuperación a un punto en el tiempo (PITR).<br>2. Transacciones con bloqueo optimista o actualización atómica y reserva de stock al crear el pedido.<br>3. Índices, paginación obligatoria, timeouts de consulta y caché (por ejemplo, Redis) para los productos más vistos. |
