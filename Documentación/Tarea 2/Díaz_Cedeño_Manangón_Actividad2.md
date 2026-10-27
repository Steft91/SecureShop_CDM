|**DEPARTAMENTO:**|**Ciencias de la Computación**|**CARRERA:**|**SOFT**|**WARE**||
|---|---|---|---|---|---|
|**ASIGNATURA:**|Software Seguro|**NIVEL:**|7mo|**FECHA:**|12/10/2026|
|**DOCENTE:**|Ing. Ángel Cudco|**TAREA N°:**|2|**CALIFICACIÓN:**||



# **Actividad de Aprendizaje: SGSI del Proyecto Integrador** 

Zaith Alejandro Manangón Vinueza Stefany Maricela Díaz Antun Andrés Isaias Cedeño Cuenca 

## **1. Antecedentes** 

# **PROYECTO INTEGRADOR** 

El proyecto integrador consiste en el diseño, desarrollo y evaluación de una aplicación de salas de chat seguras, orientada a aplicar de manera práctica los principios de desarrollo seguro de software, protección de comunicaciones, control de acceso y seguridad de contenidos multimedia. 

La solución deberá permitir que un administrador autenticado mediante usuario y contraseña gestione las salas de comunicación. El administrador podrá crear nuevas salas especificando un identificador único, clave de acceso, número máximo de participantes y el tipo de comunicación permitido, que podrá ser texto, multimedia o ambos. 

Cada usuario deberá conectarse a una sala desde un único dispositivo, implementando los mecanismos necesarios para controlar las sesiones activas y evitar conexiones simultáneas no autorizadas. El acceso a cada sala deberá estar condicionado a la validación de su identificador y clave correspondiente. 

Toda la información intercambiada dentro de las salas deberá protegerse mediante mecanismos criptográficos, garantizando como mínimo la confidencialidad, integridad y autenticidad de las comunicaciones. El equipo deberá justificar los algoritmos, protocolos, mecanismos de gestión de claves y controles implementados para proteger los mensajes durante su transmisión. 

Para las salas que permitan contenido multimedia, la aplicación deberá incorporar un mecanismo de análisis y validación de archivos. Como requerimiento particular de seguridad, el sistema deberá ser capaz de identificar archivos sospechosos o modificados mediante técnicas de esteganografía, generando alertas, registros de auditoría y aplicando una política definida por el equipo, como bloqueo, cuarentena o rechazo del archivo. 

## **2. Desarrollo** 

### **2.1. Contexto y alcance** 

**Organización** : Sistema de comunicación digital mediante salas de chat seguras. 

**Alcance del SGSI** : Aplicación de salas de chat, gestión administrativa, autenticación de usuarios, control de sesiones, comunicaciones cifradas, transferencia de archivos multimedia y mecanismos de auditoría. 

**Activos críticos:** Credenciales, mensajes, archivos multimedia, claves criptográficas, sesiones, información de salas y disponibilidad del servicio. 

### **2.2. Método de análisis** 

### **_2.2.1. Activos, amenazas y vulnerabilidades_** 

|**N.º**|**Activo (categoría)**|**Amenaza específica**|**Vulnerabilidad específica**|
|---|---|---|---|
|**1**|Claves de acceso de las<br>salas<br>privadas<br>(Información)|Obtención de claves de salas<br>mediante una filtración de la<br>configuración.|Las claves se almacenan en texto plano<br>dentro de los registros de configuración<br>de las salas.|
|**2**|Claves criptográficas de<br>las<br>comunicaciones<br>(Información)|Exposición de claves utilizadas<br>para proteger los mensajes.|Las claves criptográficas se encuentran<br>incorporadas directamente en el código<br>fuente del proyecto.|
|**3**|Registros de auditoría de<br>ingreso y salida de salas<br>(Información)|Eliminación de evidencias de<br>accesos no autorizados.|Los registros pueden ser modificados o<br>eliminados por la misma cuenta que<br>ejecuta la aplicación.|
|**4**|Módulo de autenticación<br>del<br>administrador<br>(Software)|Ataque de fuerza bruta contra<br>las credenciales administrativas.|El módulo permite intentos ilimitados<br>de<br>inicio<br>de sesión sin bloqueo<br>temporal.|
|**5**|Módulo de autorización<br>para crear y modificar<br>salas (Software)|Creación o modificación de<br>salas por usuarios sin privilegios<br>administrativos.|Los endpoints administrativos validan la<br>autenticación, pero no comprueban el<br>rol del solicitante.|
|**6**|Módulo de detección de<br>esteganografía<br>en<br>imágenes (Software)|Ingreso<br>de<br>imágenes<br>con<br>información oculta sin generar<br>alertas de seguridad.|El<br>módulo<br>analiza<br>únicamente<br>extensiones<br>y<br>metadatos,<br>sin<br>inspeccionar<br>posibles<br>alteraciones<br>esteganográficas del contenido.|
|**7**|Servicio de mensajería en<br>tiempo real (Servicio)|Interceptación<br>de<br>mensajes<br>intercambiados<br>entre<br>participantes.|El<br>servicio<br>permite<br>conexiones<br>WebSocket sin cifrado mediante ws://.|



|**8**|Servicio de ingreso a salas<br>privadas (Servicio)|Acceso automatizado a salas<br>mediante pruebas sucesivas de<br>claves.|El servicio no limita los intentos fallidos<br>de ingreso a una sala.|
|---|---|---|---|
|**9**|Servicio de transferencia<br>de archivos multimedia<br>(Servicio)|Distribución<br>de<br>archivos<br>maliciosos<br>disfrazados<br>de<br>imágenes.|El<br>servicio<br>válida<br>únicamente<br>la<br>extensión del archivo y no comprueba<br>su contenido real.|
|**10**|Servidor de aplicaciones<br>que<br>mantiene<br>las<br>conexiones<br>de<br>chat<br>(Infraestructura)|Saturación de conexiones que<br>provoca la indisponibilidad de<br>las salas.|El servidor no establece límites de<br>conexiones simultáneas por cliente.|
|**11**|Servidor de base de datos<br>de<br>salas<br>y<br>usuarios<br>(Infraestructura)|Acceso no autorizado a la base<br>de datos mediante credenciales<br>de la aplicación comprometidas.|La cuenta de conexión de la aplicación<br>posee<br>permisos<br>administrativos<br>innecesarios sobre la base de datos.|
|**12**|Directorio<br>de<br>almacenamiento<br>de<br>archivos<br>multimedia<br>(Infraestructura)|Descarga de archivos privados<br>mediante acceso directo a sus<br>direcciones.|El directorio de archivos compartidos<br>está<br>expuesto<br>públicamente<br>sin<br>validación de permisos por sala.|
|**13**|Datos de sesiones activas<br>por usuario y dispositivo<br>(Datos)|Uso simultáneo de una cuenta<br>desde<br>dos<br>dispositivos<br>diferentes.|El registro de una nueva sesión no<br>comprueba si existe otra sesión activa<br>del mismo usuario.|
|**14**|Datos<br>de<br>mensajes<br>asociados<br>a cada sala<br>(Datos)|Alteración<br>o<br>inserción<br>de<br>mensajes en una sala a la que el<br>remitente no pertenece.|El backend acepta el identificador de<br>sala enviado por el cliente sin verificar<br>su pertenencia a ella.|
|**15**|Datos de configuración del<br>cupo<br>máximo<br>de<br>participantes (Datos)|Superación del número máximo<br>de usuarios permitido en una<br>sala.|La verificación del cupo y el registro de<br>nuevos participantes se ejecutan por<br>separado, sin control de concurrencia.|



_Tabla 1. Activos, Amenazas y vulnerabilidades_ 

### **_2.2.2. Análisis de Riesgo_** 

### **Método de cálculo:** 

### 𝑅 = 𝑃 𝑥 𝐼 

Donde P representa la probabilidad de ocurrencia e I el impacto que tendría la materialización de la amenaza. Ambos se valoran del 1 al 5, obteniendo un nivel de riesgo entre 1 y 25, basándonos en la siguiente matriz: 



<!-- Start of picture text -->
(eae ea Es<br>Cs oa<br>= ES)<br>‘-[2 | = [2<br>DearS ==<br>; ee os me<br>0S eres loo<br>| es«|<br><!-- End of picture text -->

_Figura 1. Matriz de riesgos 5 x 5_ 

|**N.**|**Riesgo**|**P**|**I**|**Nivel**|
|---|---|---|---|---|
|**1**|Ingreso no autorizado a salas privadas<br>debido a la exposición de sus claves de<br>acceso almacenadas en texto plano.|**4**|**4**|**16 - Alto**|
|**2**|Pérdida de confidencialidad de los<br>mensajes cifrados por exposición de<br>claves criptográficas incluidas en el<br>código fuente.|**4**|**5**|**20 - Crítico**|
|**3**|Pérdida de trazabilidad de accesos<br>indebidos debido a la eliminación o<br>manipulación de registros de auditoría.|**3**|**4**|**12 - Medio-alto**|
|**4**|Acceso<br>no<br>autorizado<br>al<br>panel<br>administrativo<br>mediante<br>el<br>descubrimiento<br>automatizado<br>de<br>contraseñas.|**4**|**5**|**20 - Crítico**|



|**5**|Creación o modificación de salas por<br>usuarios comunes mediante solicitudes<br>directas a funciones administrativas sin<br>verificación de roles.|**4**|**4**|**16 - Alto**|
|---|---|---|---|---|
|**6**|Distribución<br>no<br>detectada<br>de<br>información<br>oculta<br>en<br>imágenes<br>manipuladas<br>mediante<br>técnicas<br>de<br>esteganografía.|**3**|**4**|**12 - Medio-alto**|
|**7**|Exposición de conversaciones privadas<br>por<br>interceptación<br>de<br>mensajes<br>transmitidos<br>mediante<br>conexiones<br>WebSocket sin cifrar.|**4**|**5**|**20 - Crítico**|
|**8**|Ingreso de usuarios no autorizados a<br>salas<br>privadas<br>mediante<br>intentos<br>automatizados de claves de acceso.|**4**|**4**|**16 - Alto**|
|**9**|Distribución de archivos maliciosos<br>entre<br>participantes<br>debido<br>a<br>una<br>validación insuficiente de los archivos<br>multimedia cargados.|**4**|**4**|**16 - Alto**|
|**10**|Interrupción del servicio de mensajería<br>por<br>agotamiento<br>de<br>conexiones<br>y<br>recursos del servidor.|**4**|**3**|**12 - Medio-alto**|
|**11**|Exposición o modificación no autorizada<br>de información de usuarios y salas<br>mediante el uso indebido de credenciales<br>con privilegios excesivos en la base de<br>datos.|**3**|**5**|**15 - Alto**|
|**12**|Filtración<br>de<br>archivos<br>multimedia<br>privados mediante el acceso directo a<br>directorios<br>de<br>almacenamiento<br>sin<br>controles de autorización.|**4**|**4**|**16 - Alto**|
|**13**|Incumplimiento de la restricción de<br>dispositivo<br>único<br>debido<br>al<br>establecimiento de sesiones simultáneas<br>de una misma cuenta.|**4**|**3**|**12 - Medio-alto**|
|**14**|Alteración<br>de<br>la<br>integridad<br>de<br>conversaciones privadas mediante la<br>inserción de mensajes por usuarios que<br>no pertenecen a la sala.|**3**|**4**|**12 - Medio-alto**|
|**15**|Superación del límite de participantes<br>configurado<br>debido<br>al<br>registro<br>concurrente<br>de<br>usuarios<br>sin<br>una<br>validación atómica del cupo.|**3**|**3**|**9 - Medio**|



_Tabla 2. Análisis y evaluación de riesgos identificados en el proyecto_ 

### **_2.2.3. Tratamiento_** 

|**N.**|**Riesgo**|**Tratamiento**|
|---|---|---|
|**1**|Ingreso no autorizado a salas privadas debido a<br>la<br>exposición<br>de<br>sus claves de acceso<br>almacenadas en texto plano.|Implementar el almacenamiento seguro<br>de las claves de acceso a las salas<br>mediante el algoritmo de hashing<br>Argon2id, utilizando una sal aleatoria<br>única para cada clave y restringiendo el<br>acceso a los registros de configuración.|
|**2**|Pérdida de confidencialidad de los mensajes<br>cifrados por exposición de claves criptográficas<br>incluidas en el código fuente.|Almacenar las claves criptográficas en<br>un gestor de secretos externo al código<br>fuente, aplicar permisos mínimos y<br>establecer mecanismos de rotación y<br>revocación de claves comprometidas.|
|**3**|Pérdida de trazabilidad de accesos indebidos<br>debido a la eliminación o manipulación de<br>registros de auditoría.|Centralizar los registros de auditoría en<br>un<br>almacenamiento<br>separado,<br>con<br>permisos de solo escritura para la<br>aplicación,<br>acceso<br>restringido<br>y<br>mecanismos<br>de<br>detección<br>de<br>modificaciones.|
|**4**|Acceso no autorizado al panel administrativo<br>mediante el descubrimiento automatizado de<br>contraseñas.|Implementar autenticación multifactor<br>(MFA), limitar los intentos fallidos de<br>inicio de sesión y aplicar retrasos<br>progresivos y bloqueos temporales ante<br>intentos sospechosos.|
|**5**|Creación o modificación de salas por usuarios<br>comunes<br>mediante<br>solicitudes<br>directas<br>a<br>funciones administrativas sin verificación de<br>roles.|Implementar control de acceso basado<br>en roles, verificando en el servidor los<br>permisos<br>administrativos<br>en<br>cada<br>operación de creación, modificación y<br>eliminación de salas.|
|**6**|Distribución no detectada de información oculta<br>en imágenes manipuladas mediante técnicas de<br>esteganografía.|Implementar un análisis del contenido<br>de las imágenes mediante técnicas de<br>estegoanálisis (análisis estadístico de<br>bits menos significativos y de entropía)<br>y sanitizar cada imagen aceptada<br>recodificándola<br>y<br>eliminando<br>sus<br>metadatos; los archivos sospechosos se<br>colocarán<br>en<br>cuarentena,<br>con<br>generación de alertas y registro de<br>auditoría del evento.|
|**7**|Exposición de conversaciones privadas por<br>interceptación<br>de<br>mensajes<br>transmitidos<br>mediante conexiones WebSocket sin cifrar.|Exigir el uso de WebSocket sobre TLS<br>1.3 (wss://) con certificados válidos,<br>rechazar las conexiones ws://, aplicar<br>HSTS y validar el encabezado Origin,<br>además de cifrar el contenido de cada|



|||mensaje con un esquema autenticado<br>(AES-256-GCM)<br>para<br>garantizar<br>confidencialidad,<br>integridad<br>y<br>autenticidad.|
|---|---|---|
|**8**|Ingreso de usuarios no autorizados a salas<br>privadas mediante intentos automatizados de<br>claves de acceso.|Limitar los intentos fallidos de ingreso<br>por dirección IP, dispositivo y sala,<br>aplicando<br>retrasos<br>progresivos<br>y<br>bloqueos<br>temporales,<br>exigir<br>una<br>longitud y complejidad mínimas a las<br>claves de acceso, y registrar y alertar<br>los intentos fallidos repetidos.|
|**9**|Distribución de archivos maliciosos entre<br>participantes<br>debido<br>a<br>una<br>validación<br>insuficiente<br>de<br>los<br>archivos<br>multimedia<br>cargados.|Validar el tipo real de cada archivo<br>mediante su firma (magic bytes) contra<br>una lista blanca de formatos, limitar su<br>tamaño, analizarlo con un motor<br>antimalware<br>y<br>almacenarlo<br>con<br>nombres aleatorios en un directorio sin<br>permisos de ejecución.|
|**10**|Interrupción del servicio de mensajería por<br>agotamiento de conexiones y recursos del<br>servidor.|Establecer<br>límites<br>de<br>conexiones<br>simultáneas por cliente y por dirección<br>IP, limitar la tasa y el tamaño de los<br>mensajes,<br>cerrar<br>las<br>conexiones<br>inactivas mediante timeouts y delegar<br>la protección perimetral a un proxy<br>inverso con monitoreo y alertas de<br>consumo de recursos.|
|**11**|Exposición o modificación no autorizada de<br>información de usuarios y salas mediante el uso<br>indebido<br>de<br>credenciales<br>con<br>privilegios<br>excesivos en la base de datos.|Aplicar<br>el<br>principio<br>de<br>mínimo<br>privilegio: la cuenta de la aplicación<br>tendrá solo los permisos necesarios<br>(SELECT,<br>INSERT,<br>UPDATE<br>y<br>DELETE sobre las tablas requeridas),<br>sin permisos administrativos ni de<br>modificación de esquema. Se usarán<br>cuentas separadas para migraciones y<br>administración. Las credenciales se<br>guardarán en un gestor de secretos con<br>rotación periódica, y la base de datos se<br>aislará en una red interna, con registro<br>de consultas privilegiadas.|
|**12**|Filtración de archivos multimedia privados<br>mediante el acceso directo a directorios de<br>almacenamiento sin controles de autorización.|Mover el almacenamiento fuera del<br>directorio<br>público<br>y entregar los<br>archivos mediante un endpoint que<br>valide la sesión y la pertenencia del<br>usuario a la sala. Se usarán URLs<br>firmadas con expiración corta, nombres<br>de archivo aleatorios y se deshabilitará<br>el listado de directorios.|
|**13**|Incumplimiento de la restricción de dispositivo<br>único debido al establecimiento de sesiones|Verificar en el servidor, al crear una<br>sesión, si el usuario ya tiene una activa,|



||simultáneas de una misma cuenta.|y aplicar la política definida (rechazar<br>el nuevo ingreso o invalidar la sesión<br>anterior). Se agregará una restricción<br>única en base de datos para la sesión<br>activa por usuario, tokens vinculados al<br>dispositivo, expiración por inactividad<br>y registro de auditoría de los intentos.|
|---|---|---|
|**14**|Alteración de la integridad de conversaciones<br>privadas mediante la inserción de mensajes por<br>usuarios que no pertenecen a la sala.|Derivar la sala y el usuario desde la<br>sesión autenticada en el servidor, sin<br>confiar en el identificador enviado por<br>el cliente, y verificar la pertenencia<br>antes de aceptar cada mensaje. Se<br>incluirán el identificador de sala y de<br>remitente como datos autenticados<br>adicionales (AAD) en AES-256-GCM,<br>y se registrarán y alertarán los intentos<br>rechazados.|
|**15**|Superación<br>del<br>límite<br>de<br>participantes<br>configurado debido al registro concurrente de<br>usuarios sin una validación atómica del cupo.|Unificar la verificación del cupo y el<br>registro del participante en una sola<br>operación<br>atómica,<br>mediante<br>una<br>transacción<br>con<br>bloqueo<br>de<br>fila<br>(SELECT ... FOR UPDATE) o un<br>incremento condicional. Se reforzará<br>con una restricción a nivel de base de<br>datos y pruebas de concurrencia.|



_Tabla 3. Tabla de tratamiento por riesgo_ 

**_2.2.4. Medición del riesgo residual_** 

|**N.**|**Riesgo**|**Inicial**|**Residual**|**Estado**|
|---|---|---|---|---|
|**1**|Ingreso no autorizado a salas privadas debido<br>a la exposición de sus claves de acceso<br>almacenadas en texto plano.|**16**|**8**|**Medio**|
|**2**|Pérdida de confidencialidad de los mensajes<br>cifrados<br>por<br>exposición<br>de<br>claves<br>criptográficas incluidas en el código fuente.|**20**|**5**|**Medio**|
|**3**|Pérdida de trazabilidad de accesos indebidos<br>debido a la eliminación o manipulación de<br>registros de auditoría.|**12**|**4**|**Bajo**|
|**4**|Acceso no autorizado al panel administrativo<br>mediante el descubrimiento automatizado de<br>contraseñas.|**20**|**5**|**Medio**|
|**5**|Creación o modificación de salas por usuarios<br>comunes mediante solicitudes directas a<br>funciones administrativas sin verificación de<br>roles.|**16**|**4**|**Bajo**|



|**6**|Distribución no detectada de información<br>oculta en imágenes manipuladas mediante<br>técnicas de esteganografía.|**12**|**8**|**Medio**|
|---|---|---|---|---|
|**7**|Exposición de conversaciones privadas por<br>interceptación<br>de<br>mensajes<br>transmitidos<br>mediante conexiones WebSocket sin cifrar.|**20**|**4**|**Bajo**|
|**8**|Ingreso de usuarios no autorizados a salas<br>privadas mediante intentos automatizados de<br>claves de acceso.|**16**|**8**|**Medio**|
|**9**|Distribución de archivos maliciosos entre<br>participantes<br>debido<br>a<br>una<br>validación<br>insuficiente de los archivos multimedia<br>cargados.|**16**|**6**|**Medio**|
|**10**|Interrupción del servicio de mensajería por<br>agotamiento de conexiones y recursos del<br>servidor.|**12**|**6**|**Medio**|
|**11**|Exposición o modificación no autorizada de<br>información de usuarios y salas mediante el<br>uso indebido de credenciales con privilegios<br>excesivos en la base de datos.|**15**|**5**|**Medio**|
|**12**|Filtración de archivos multimedia privados<br>mediante el acceso directo a directorios de<br>almacenamiento sin controles de autorización.|**16**|**4**|**Bajo**|
|**13**|Incumplimiento<br>de<br>la<br>restricción<br>de<br>dispositivo único debido al establecimiento de<br>sesiones simultáneas de una misma cuenta.|**12**|**3**|**Bajo**|
|**14**|Alteración de la integridad de conversaciones<br>privadas mediante la inserción de mensajes<br>por usuarios que no pertenecen a la sala.|**12**|**4**|**Bajo**|
|**15**|Superación<br>del<br>límite<br>de<br>participantes<br>configurado debido al registro concurrente de<br>usuarios sin una validación atómica del cupo.|**9**|**3**|**Bajo**|



_Tabla 4. Tabla de medición de riesgo residual_ 

## **3. Conclusiones** 

El análisis de los 15 activos identificados en la aplicación de salas de chat seguras permitió evaluar el riesgo inicial de cada amenaza mediante la matriz 5 x 5 (R = P x I). Antes de aplicar controles, 3 riesgos se ubicaron en nivel Crítico, 6 en nivel Alto, 5 en nivel Medio-alto y 1 en nivel Medio, es decir, 14 de los 15 riesgos estaban en niveles Medio-alto o superiores. 

Los riesgos críticos corresponden a la exposición de las claves criptográficas en el código fuente, el descubrimiento automatizado de contraseñas del administrador y el uso de WebSocket sin cifrar. Estos tres afectan directamente la confidencialidad de las comunicaciones y el control administrativo, que son los pilares del proyecto, por lo que se priorizaron en el tratamiento. 

Finalmente, el tratamiento solo reduce el riesgo si los controles se implementan y se verifican. Se recomienda validarlos mediante pruebas de seguridad,  revisar esta evaluación cuando cambie la arquitectura de la aplicación o aparezcan nuevas amenazas. 

## **4. Referencias** 

- Biryukov, A., Dinu, D., & Khovratovich, D. (2021). _Argon2: the memory-hard function for password hashing and other applications_ (RFC 9106). Internet Engineering Task Force. https://www.rfc-editor.org/info/rfc9106 

OWASP Foundation. (2021). _OWASP Top 10:2021_ . https://owasp.org/Top10/ 

- OWASP Foundation. (s. f.). _Password storage cheat sheet_ . OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html 

