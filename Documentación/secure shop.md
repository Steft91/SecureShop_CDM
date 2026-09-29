DEPARTAMENT Ciencias de la Computación CARRERA: SOFTWARE
O:
ASIGNATURA: Software Seguro NIVEL: 7mo FECHA: 29/09/2026
DOCENTE: Ing. Ángel Cudco TAREA N°: 1 CALIFICACIÓ
N:
Actividad de Aprendizaje: Reconocimiento de activo
Zaith Alejandro Manangón Vinueza
Stefany Maricela Díaz Antun
Andrés Isaias Cedeño Cuenca
Antecedentes
SecureShop es una empresa ficticia dedicada a la comercialización de productos tecnológicos a través de Internet.
Debido al crecimiento de sus operaciones, requiere desarrollar una nueva plataforma web que permita administrar
usuarios, productos y pedidos.
La empresa ha decidido construir la solución utilizando una arquitectura basada en microservicios, debido a que
desea que sus componentes puedan desarrollarse, desplegarse y evolucionar independientemente.

El equipo de desarrollo deberá construir progresivamente una primera versión de la aplicación SecureShop,
compuesta por servicios independientes para la administración de usuarios, productos y pedidos, una base de datos
para cada dominio y un punto de entrada común para las solicitudes de los clientes.
Paralelamente al desarrollo funcional, el equipo deberá analizar los aspectos de seguridad que aparecen durante el
ciclo de vida del software, identificando activos, vulnerabilidades potenciales, amenazas, riesgos, propiedades de
seguridad, puntos de exposición y dependencias entre los diferentes componentes.
Desarrollo
Actividad 1:
1.-  Crear un repositorio de Github
2.-  Identificar al menos diez activos de SecureShop.
Por ejemplo:
| ●  Información de usuarios  |     |     |     |     |     |     |
| --------------------------- | --- | --- | --- | --- | --- | --- |
| ●  Credenciales             |     |     |     |     |     |     |
| ●  Catálogo de productos    |     |     |     |     |     |     |
3.-  Clasificar cada activo según:
| ●  información;      |     |     |     |     |     |     |
| -------------------- | --- | --- | --- | --- | --- | --- |
| ●  software;         |     |     |     |     |     |     |
| ●  servicio;         |     |     |     |     |     |     |
| ●  infraestructura;  |     |     |     |     |     |     |
| ●  datos.            |     |     |     |     |     |     |
4.-  Responder:
¿Qué consecuencias tendría para SecureShop que este activo fuera accedido, modificado o quedará indisponible?
| Activo             | Tipo         | Consecuencia de ….  |     |     |     |     |
| ------------------ | ------------ | ------------------- | --- | --- | --- | --- |
| Datos de usuarios  | Información  |                     |     |     |     |     |
| Credenciales       | Información  |                     |     |     |     |     |
sensible

| N.  Activo  |     | Tipo  | Consecuencia de ….  |     |     |     |
| ----------- | --- | ----- | ------------------- | --- | --- | --- |
1  Información  de  un  Información  Se expone el historial de compras y las direcciones
Pedido
de clientes, se pueden alterar los mismos (montos,
|     |     |     | cantidades,  | destino)  que  | derivan  | en  fraude  y  |
| --- | --- | --- | ------------ | -------------- | -------- | -------------- |
pérdidas económicas.
2  Logs  y  registros  de  Datos  Pueden filtrar tokens, IPs o datos personales si se
auditoría  registran de más, con un atacante se puede perder
evidencia forense.

3  API Gateway  Servicio  Es el punto de entrada único: un fallo de control
|     | permite  | llegar  a  | todos  los  microservicios,  |                 | si  |
| --- | -------- | ---------- | ---------------------------- | --------------- | --- |
|     | quedara  | fuera  de  | servicio,  toda              | la  plataforma  |     |
queda caída
4  Microservicios  Servicio  Operaciones sin autenticación funciones como por
|     | ejemplo  | “listar  usuarios”  | quedan  | expuestas  | a   |
| --- | -------- | ------------------- | ------- | ---------- | --- |
cualquiera, Si llega a ser modificado la lógica de
|     | negocio  | se  altera, se pierde la función de ese  |     |     |     |
| --- | -------- | ---------------------------------------- | --- | --- | --- |
dominio (ejm: sin ProductService no se pueden
completar y crear los pedidos)
5  Base de datos de  Datos  Se  expone  el  inventario,  catálogo  completo,
| productos  | registros  | corruptos,  | productos  | a   | precios  |
| ---------- | ---------- | ----------- | ---------- | --- | -------- |
incorrectos, product Service no responde
6  Variables de entorno  Información sensible   Acceso  directo  a  la  base  de  datos  con  la
posibilidad de generar montos, perfiles falsos
7  Respaldos  Datos  Filtración masiva, es una copia completa de todo
|     | el  código,  | se  podría  | restaurar  | un  | backup  |
| --- | ------------ | ----------- | ---------- | --- | ------- |
modificado con datos corruptos
8  Red  y  canales  de  Infraestructura  Intercepción de tráfico sobre HTTP, peticiones y
| comunicación  | respuestas alteradas en tránsito.  |     |     |     |     |
| ------------- | ---------------------------------- | --- | --- | --- | --- |
Los servicios no se logran comunicar entre sí
9  Base  de  datos  de  Datos  Si se accediera a los datos existiera filtración de
| usuarios  | todo el padrón de clientes junto con los hashes.  |     |     |     |     |
| --------- | ------------------------------------------------- | --- | --- | --- | --- |
si se modificara, quedarían registros corruptos o
cuentas inyectadas
Y si quedará indisponible el User Service caería
junto con el login y registro
10  Código  fuente  Software  Con el acceso al software se revelaría la lógica y
| (repositorio GitHub)  | las posibles vulnerabilidades.  |     |     |     |     |
| --------------------- | ------------------------------- | --- | --- | --- | --- |
Si existen modificaciones hubieran Inyecciones de
backdoors o código malicioso en el despliegue
|     | Al  quedar  | indisponible  | no  se  | podría  corregir,  |     |
| --- | ----------- | ------------- | ------- | ------------------ | --- |
desplegar ni evolucionar el sistema
11  Servidores /  Infraestructura  Si se accede al root sin autorización se podría
contenedores / nube  perder el control de todos los servicios y BD
|     | Si  se  | modificara  | la  infraestructura,  |     | su  |
| --- | ------- | ----------- | --------------------- | --- | --- |
donde se despliega
|     | configuración      | quedaría alterada con malware o  |     |     |     |
| --- | ------------------ | -------------------------------- | --- | --- | --- |
|     | minería de datos.  |                                  |     |     |     |
Y al quedar indisponible habría caída total del
sistema

12  Credenciales  Información  Al acceder a la información existiría suplantación
| de  identidad,  | secuestro  | de  cuentas  | y  compras  |
| --------------- | ---------- | ------------ | ----------- |
(contraseñas hasheadas,
fraudulentas
tokens de sesión/JWT)
Al haber modificación en la información alguien
| podría  toma  | el  control  | de  cuentas  | o  escalar  |
| ------------- | ------------ | ------------ | ----------- |
privilegios (volverse admin)
| Y  al  quedar  | indisponible,  | nadie  podrá  | iniciar  |
| -------------- | -------------- | ------------- | -------- |
sesión y el sistema quedará inutilizable