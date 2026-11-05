DEPARTAMENTODECIENCIASDELACOMPUTACIÓN
DESARROLLOSOFTWARESEGURO
PROYECTOINTEGRADORDELPRIMERPARCIAL
Backend:AutenticaciónJWT/RBACydeteccióndeesteganografía
Fechadeentrega:04/11/2026
Resumen
Resumen.LaprimeraentregadelProyectoIntegradortieneporfinalidaddiseñar,implementary
evaluarelbackendinicialdeunaaplicacióndesalasdechatseguras.Elproductoexigidoconsta
dedosmicroserviciosRESTindependientes:unodeautenticaciónyautorizaciónqueadministra
usuarios,rolesysurelaciónmuchosamuchos(N:M),emitetokensJSONWebToken(JWT)yaplica
controldeaccesobasadoenroles(RBAC);yotrodedeteccióndeesteganografíaquevalidayanaliza
imágenesexclusivamentedespuésdecomprobarlaidentidadylaautorizaciónvigentedelsolicitante.
Eldesarrollodebeaportarcódigoejecutable,documentaciónarquitectónicaypruebasreproducibles
deseguridadeintegración,bajolosenfoquesZeroTrust,SecurebyDesignyShiftLeftSecurity.
Palabrasclave:microservicios;JWT;RBAC;controldeacceso;esteganografía;desarrolloseguro.
1. Descripcióndelproblemayobjetivos
Elproyectointegradorgeneralproponeeldiseñoydesarrollodeunaplataformadesalasdechatseguras
concontrolesdeacceso,proteccióndecomunicacionesyvalidacióndecontenidomultimedia.Sinembar-
go,antesdeimplementarlassalasylamensajería,resultanecesariodisponerdeserviciosdeidentidady
análisisdearchivosqueincorporenlaseguridaddesdesuarquitectura.Enparticular,laautenticación
debedistinguirsedelaautorización:unJWTválidoidentificaunasesiónounsujeto,peronobastapor
sísoloparademostrarquelospermisosdelusuariocontinúanvigentes.Delmismomodo,losarchivos
recibidosdeclientesexternosnodebenconsiderarseconfiablesyrequierenvalidacionespreviasasu
procesamiento.
Laprimeraversiónabordaráestasnecesidadesmedianteunaseparaciónexplícitaderesponsabilidades.
AUTHcentralizarálaadministracióndeidentidadesylasdecisionesRBACapartirdeunabasededatos
relacional,mientrasqueSTEGOrecibiráyexaminaráarchivosdeimagensinaccederdirectamentea
las tablas de identidad. Dicha separación deberá limitar privilegios, reducir acoplamiento y permitir
comprobarquelamodificaciónorevocaciónderolesproduceefectosinmediatosenlasnuevassolicitudes
protegidas.EldiseñotomarácomoreferenciaslosprincipiosdeISO/IEC27001eISO/IEC27034,sinafirmar
certificaciónnicumplimientonormativointegral[1,2].
1.1 Objetivogeneral
Diseñar,implementar,integraryevaluardosmicroserviciosindependientesqueconstituyanelBackend
V1deunaaplicacióndechatsegura:unmicroserviciodeautenticaciónyautorizaciónmedianteJWTy
RBAC,fundamentadoenlasentidadespersistidasusers,rolesyuser_roles,yunmicroserviciode
DCCO|DesarrolloSoftwareSeguro Página1de8

deteccióndeesteganografíaqueanaliceimágenesúnicamentedespuésdevalidarlascredencialesylos
privilegiosvigentesdelusuario.
1.2 Objetivosespecíficos
Eldesarrollodeberádemostrarqueelequipoescapazdemodelarunarelacióndemuchosamuchos
(N:M)entreusuariosyroles;implementarcredencialesprotegidas,JWTfirmadosydecisionesdeautoriza-
ciónbasadasenlosdatosactuales;exponerunaAPIdeanálisisdeimágenesqueejecutealmenosuna
técnicadedetecciónesteganográficaverificable;diseñarlaintegraciónseguraentreserviciossincompartir
indebidamentelastablasocredencialesdeAUTH;ydocumentarpruebasfuncionales,deseguridadyde
integraciónrelacionadasconlosriesgosidentificados.
1.3 Alcancedelaprimeraversión
La primera entrega no comprende la interfaz web o móvil, la creación y administración de salas, la
mensajería en tiempo real, el cifrado de extremo a extremo del chat ni la restricción de dispositivos
delosparticipantes.Estascaracterísticascorrespondenaetapasposterioresdelproyectogeneral.En
consecuencia,laevaluaciónselimitaráalfuncionamientosegurodelosdosmicroservicios,susinterfaces,
lapersistencianecesariaylaevidenciareproducibledesuintegración.
2. Indicacionestécnicasydedesarrollo
2.1 Arquitecturaeindependenciadeservicios
Lasolucióndeberáorganizarseendosaplicacionesbackendconprocesosdeejecución,archivosde
configuración,endpointsydocumentaciónindependientes.Podránimplementarseconelmismolenguaje
ocontecnologíasdiferentes,siemprequelaselecciónresultejustificada.Laimplementacióndedos
carpetasdentrodeunasolaaplicaciónnosatisfaráelrequisitoarquitectónico:AUTHySTEGOdeberán
iniciarse,detenerseydesplegarsedemaneraautónoma.Parafacilitarsuevaluación,ambosservicios
deberánestardefinidosmediantecontenedoresseparadosenDocker Compose.Unabasededatosoun
volumendealmacenamientoseconsideraráninfraestructuradeapoyo,nountercermicroservicio.
ClientedepruebasREST
AUTH STEGO
Autorizaciónvigente
Usuarios,rolesyasignacionesN:M Validacióndeimágenes
JWTyautorizaciónRBAC Análisisyregistroesteganográfico
PersistenciaexclusivadeAUTH ResultadosyarchivosdeSTEGO
Figura1:Separaciónderesponsabilidadesycomunicaciónentrelosdosmicroservicios.
2.2 Microserviciodeautenticaciónyautorización(AUTH)
AUTHserálaúnicaautoridadencargadadeadministrarlasidentidadesyroles.Sumodelodedatos
incluirálasentidadesusers(identificador,nombredeusuario,correoelectrónico,hashdecontraseña,
estadoydatosdeauditoría),roles(identificador,nombre,descripciónyestado)yuser_roles(identifi-
cador,referenciasausuarioyrol,yfechadeasignación).SeimplementaráunarelaciónN:Mmediante
clavesforáneashacialasdosentidadesprincipalesyunarestricciónUNIQUE(user_id, role_id)que
eviteduplicaciones.Unmismousuariopodrárecibirvariosrolesyunmismorolpodráasignarseadistintos
usuarios.
Eliniciodesesiónvalidarálascredencialescontralosusuariospersistidos,cuyascontraseñasdeberán
DCCO|DesarrolloSoftwareSeguro Página2de8

almacenarseconArgon2idobcrypt.LosJWTdeberánestarfirmados,poseertiempodeexpiraciónacotado
ycontenerunidentificadordeusuarioensub.Elequipodocumentaráelalgoritmoautorizado,lagestión
declavesyloscontrolessobrefirma,emisor,audienciayvigencia,tomandocomoreferencialasbuenas
prácticascorrespondientes[5,7].Serecomiendaemplearfirmaasimétrica,conservandolaclaveprivada
únicamenteenAUTHypermitiendoaSTEGOverificartokensconlaclavepública.
LaautorizaciónRBACseresolveráconsultandolosusuarios,rolesyasignacionesvigentes,nomediante
listasdeusuariosopermisoscodificadasenelcódigoniconfiandoexclusivamenteenrolesincluidosen
unJWTantiguo.LasoperacionesadministrativasseránexclusivasdelrolADMIN;elrolANALYSTpodrá
ejecutaranálisisyconsultarsusresultadosautorizados;yelrolUSERsólopodráaccederasuperfilya
lasoperacionesexpresamentehabilitadas.Unusuariopodráacumularroles,perocadaoperaciónestará
sujetaalprincipiodemínimoprivilegio.Laeliminaciónodesactivacióndeunaasignacióndeberáimpedir
nuevasoperacionesquerequieranesepermiso,inclusosielJWTaúnnohaexpirado.
2.3 Microserviciodedeteccióndeesteganografía(STEGO)
STEGOimplementaráunaAPIRESTindependientepararecibirarchivosdeimagenmediantemultipart/
form-data,validarextensión,firmareal,tipodecontenido,tamañoylímitesdeprocesamiento,yejecutar
almenosunatécnicaverificablededeteccióndeposiblesdatosocultos.Comoalcancemínimosetrabajará
conimágenesPNGoBMPcompatiblesconlatécnicaseleccionada,porejemplounanálisisestadísticodel
bitmenossignificativo(LSB).Elequipodeberájustificarelprocedimientoysusparámetros,implementar
loscálculoscorrespondientesyemplearmuestrasoriginalesymodificadasparaevidenciarsusresultados.
La clasificación deberá distinguir, según la evidencia, archivos sin_indicios, sospechosos, no_
concluyentesoconerror.Unresultadosospechosoconstituyeunindicio,nopruebadefinitivade
esteganografía.Cadaanálisisconservaráalmenosunidentificador,elusuariosolicitante,elhashSHA-256
delarchivo,latécnicaejecutada,losindicadorescalculados,lafecha,elresultadoylapolíticaaplicada
(rechazo,cuarentenaoadvertencia).Losarchivosdeberántratarsesinejecutarcódigorecibido,evitando
suexposiciónpúblicaycontrolandosueliminaciónoaislamiento[4].
2.4 ComunicaciónsegurayaplicacióndeRBAC
ElclienteseautenticarácontraAUTHyrecibiráunJWT;acontinuación,enviaráesetokenenlacabe-
ceraAuthorization: BearerdelassolicitudesdirigidasaSTEGO.Esteúltimocomprobarálavalidez
criptográficadeltokenysolicitaráaAUTH,medianteunendpointinternoprotegido,unadecisiónde
autorizaciónactualparalaaccióny,cuandocorresponda,elrecursosolicitado.AUTHverificaráelestado
delusuarioysusrolespersistidosyresponderáconunadecisióndepermitirodenegar.Laidentidadde
STEGOanteAUTHdeberáprotegersemedianteautenticaciónentreserviciosyuncanalseguro.Encaso
deindisponibilidaddeAUTHodeausenciadeunadecisiónverificable,STEGOrechazarálaoperaciónsin
procesarelarchivo.
ElusodeJWTnoeximeaningúnserviciodelaautorización.Pordiseño,STEGOnoconsultarádirectamen-
telabasededatosdeAUTH,noalmacenarácontraseñasnirecibirálaclaveprivadadefirma.Tampoco
deberáaceptarpermisosproporcionadosporelclienteencabecerasocamposquepuedanmanipular-
se.EstoscontrolesmaterializanlosprincipiosZeroTrustySecurebyDesign;laspruebastempranasde
credenciales,autorizaciónyarchivosreflejaránShiftLeftSecurity[8,3].
2.5 ContratomínimodelasAPIs
Latablasiguientesintetizalasrutasrequeridas.Seaceptaránprefijosdeversióncomo/api/v1sise
documentanclaramenteysemantienenlasresponsabilidadesasignadas.
Servicio Método Ruta Accesorequerido
AUTH POST /api/auth/login Público,con
limitaciones
AUTH GET /api/auth/profile Usuarioautenticado
DCCO|DesarrolloSoftwareSeguro Página3de8

| Servicio | Método   | Ruta                          | Accesorequerido   |
| -------- | -------- | ----------------------------- | ----------------- |
| AUTH     | POST     | /api/auth/logout              | Sesiónautenticada |
| AUTH     | POST/GET | /api/users                    | ADMIN             |
| AUTH     | PATCH    | /api/users/:id                | ADMIN             |
| AUTH     | POST/GET | /api/roles                    | ADMIN             |
| AUTH     | PATCH    | /api/roles/:id                | ADMIN             |
| AUTH     | POST     | /api/user-roles               | ADMIN             |
| AUTH     | DELETE   | /api/user-roles/:id           | ADMIN             |
| AUTH     | POST     | /internal/authorization/check | SóloSTEGO         |
autenticado
| STEGO | POST | /api/steganography/analyze | ADMINoANALYST     |
| ----- | ---- | -------------------------- | ----------------- |
| STEGO | GET  |                            | RBACypropiedaddel |
/api/steganography/results/:id
recurso
LaAPIdeberádevolverrespuestascoherentesycódigosHTTPapropiados:401cuandofalteonosea
válidalaautenticación,403cuandoelusuariocarezcadelpermiso,413paracargasexcesivasy415para
formatosnoadmitidos.Sedeberánregistrarloseventosrelevantessindivulgarcontraseñas,claveso
JWTcompletos.TodoslosendpointssedocumentaránconOpenAPIyseránverificablesconPostman,
Insomniaoherramientasequivalentes.
3. Entregablesypresentaciónderesultados
Laentregacomprenderáunrepositoriodecódigofuentequecontengaambasaplicacionesbackend
separadas,susdependencias,configuracionesdeejemployarchivosdeconstrucción.Deberánincluirseun
README.mdconlasinstruccionesparaclonar,configurareiniciarlosservicios;unarchivo.env.example
paracadaaplicaciónsinsecretosreales;migracionesoscriptsparaprepararlabasededatosdeAUTH;y
unarchivodocker-compose.ymlquepermitalevantarlosdosmicroserviciosdemanerareproducible.
Labasededatosyelalmacenamientodeberánpersistirlainformaciónnecesariasincomprometerlas
credencialesdelsistema.
Ladocumentacióntécnicadeberáincorporarundiagramadearquitecturaqueidentifiqueloslímitesde
confianza,lasresponsabilidadesylacomunicaciónentreAUTHySTEGO,juntoconundiagramaentidad–
relaciónquemuestrelaasociaciónN:Mentreusers,rolesyuser_roles.Tambiénseentregaráuna
explicacióndelaautenticaciónJWT,laautorizaciónRBACylaestrategiautilizadaparacomprobarroles
vigentes;unamatrizderolesypermisos;lasespecificacionesOpenAPIdeambosservicios;ylajustificación
técnicadelmétododeanálisisesteganográfico,susformatosylimitaciones.
Comoevidenciadedesarrolloseguro,losequipospresentaránunamatrizdeactivos,amenazas,vul-
nerabilidades,riesgosycontroles,vinculadaconlosenfoquesZeroTrust,SecurebyDesignyShiftLeft
SecurityyconlosprincipiospertinentesdeISO/IEC27001eISO/IEC27034.Seadjuntaránresultados
reproduciblesdepruebasunitarias,funcionales,deseguridadeintegración,unacoleccióndesolicitudes
REST,muestrasdeimágenessinmodificacionesconocidasyconinformaciónocultamedianteunatécnica
compatible,asícomoregistrosdeauditoríadepuradosdeinformaciónsensible.
Durantelasustentaciónseránecesarioejecutarambosserviciosydemostrarquecadaunoresponde
desdesupropiaAPI.Elequipodeberácrearunusuariocondosroles,asignarunroladosusuarios,iniciar
sesiónenAUTHyemplearelJWTrecibidoparaefectuarunasolicitudaSTEGO.Acontinuación,deberá
demostrarquelassolicitudessintoken,contokeninválidoosinprivilegiossondenegadas;queretirar
unrolvigenteimpideunanuevaoperaciónconelmismoJWTaúnnoexpirado;yqueSTEGOfallade
maneraseguracuandoAUTHnopuedeproporcionarunaautorizaciónválida.Finalmente,seanalizaráuna
imagendereferenciayunaimagendepruebacondatosocultoscompatiblesconeldetector,explicando
losresultadosrealesylaslimitacionesobservadas.
DCCO|DesarrolloSoftwareSeguro Página4de8

Recepciónyfechadeentrega.Eltrabajoseentregaráelmiércoles4denoviembrede2026,a
lahoradeclases.Elequipodeberápresentarelrepositorio,ladocumentaciónylasevidencias
requeridas,ydemostrarelfuncionamientodelBackendV1durantelasesión.Noseconsiderará
completaunasoluciónmonolíticapresentadacomodoscarpetas,niunadeteccióndeesteganografía
simuladasinprocesamientodearchivosreal.
4. Rúbricadeevaluación
Laevaluaciónseefectuarásobreunacalificaciónmáximade20puntosyconsiderarálaimplementación
funcional,laseguridadefectivamenteaplicada,lacalidaddeldiseñoylareproducibilidaddelasevidencias.
Serevisarátantolaejecucióndelosmicroservicioscomosucódigofuente,documentaciónyresultados
deprueba.LadistribucióndepuntajessepresentaenlaTabla2.
N.º Criterioyevidenciaverificable Puntos
1 Arquitectura.SeparaciónrealentreAUTHySTEGO,despliegueindependiente,contratosRESTyDocker 3,0
Compose.
2 Modelodeidentidad.CRUDdeusuariosyroles,asociaciónN:Mmedianteuser_roles,clavesforáneasy 3,0
unicidad.
3 AutenticaciónJWT.Validacióndecredenciales,hashingdecontraseñas,firma,expiraciónyverificación 3,0
detokens.
4 RBACeintegración.AutorizaciónvigentedesdeAUTH,permisosporrol,denegación401/403,pruebade 4,0
revocaciónyfalloseguro.
5 Deteccióndeesteganografía.Validaciónyprocesamientorealdeimágenes,técnicajustificada, 5,0
resultados,alertasopolíticayauditoría.
6 Pruebasydocumentación.OpenAPI,evidenciasreproducibles,muestras,matrizderiesgos,guíade 2,0
ejecuciónysustentación.
TOTAL 20,0
Cuadro2:Criteriosdecalificación.
Cadacriteriosecalificarádeacuerdoconelniveldelogrodemostrado:excelente(100 %),satisfactorio
(75 %),endesarrollo(50 %),insuficiente(25 %)onodemostrado(0 %).Elpuntajeobtenidoresultará
demultiplicarlaponderaciónmáximaporelporcentajecorrespondiente.Porejemplo,elcriteriodeRBAC
eintegración,conunmáximodecuatropuntos,recibirátrespuntossialcanzaelnivelsatisfactorio.La
sumadelosseiscriteriosnopodrásuperarlosveintepuntos.
5. Anexos
5.1 AnexoA.Entidadesyrelacióndemuchosamuchos
LarelaciónrequeridaparaJWT/RBACdeberáimplementarsemedianteunatablaasociativarealyrestric-
cionesdeintegridadenlabasededatos.Noseaceptaránarreglosderolesalmacenadosexclusivamente
enmemorianiasignacionescodificadascomoconstantesdeaplicación.Laestructuralógicamínimase
resumeenlaTabla3.
Entidad Atributosyrestriccionesobligatorias
users id(PK),usernameyemail(únicos),password_hash,status,created_at,updated_at.
roles id(PK),name(único),description,status,camposdeauditoría.
user_roles id(PK),user_id(FK),role_id(FK),assigned_atyUNIQUE(user_id, role_id).
Cuadro3:ModelomínimodeidentidadpertenecienteexclusivamenteaAUTH.
DCCO|DesarrolloSoftwareSeguro Página5de8

5.2 AnexoB.Contratoilustrativodeautorización
LapeticióninternaPOST /internal/authorization/checkseráinvocadaporSTEGOconautentica-
cióndeservicioycomunicaciónprotegida.AUTHvalidaránuevamentelaidentidaddelusuarioycompro-
barásusasignacionesactivasantesderesponder.Elejemplosiguienteesreferencialydebeconcretarse
enladocumentaciónOpenAPIdelequipo.
POST /internal/authorization/check
{
| "subject_token": | "<JWT_DEL_USUARIO>",     |     |     |     |
| ---------------- | ------------------------ | --- | --- | --- |
| "action":        | "steganography.analyze", |     |     |     |
| "resource_id":   | null                     |     |     |     |
}
| // Respuesta | de AUTH |     |     |     |
| ------------ | ------- | --- | --- | --- |
{
| "subject_id": | "<UUID_USUARIO>",               |     |     |     |
| ------------- | ------------------------------- | --- | --- | --- |
| "action":     | "steganography.analyze",        |     |     |     |
| "allowed":    | true,                           |     |     |     |
| "reason":     | "active_role_grants_permission" |     |     |     |
}
Losdatosdevueltosnodeberáninterpretarsecomounaautorizaciónpermanente.Cadaoperaciónprote-
gidarequeriráunadecisiónválida,ylasfallasdecomunicaciónoautenticaciónentreserviciosdeberán
resolversecondenegaciónpordefecto.
5.3 AnexoC.Contratoilustrativodeanálisis
STEGO recibirá el archivo en su endpoint de análisis mediante una solicitud POST con contenido
multipart/form-data.DespuésdecomprobarJWTyRBAC,ejecutarálatécnicaelegidayproporcionará
unregistroverificable.Losvaloresnuméricosdelejemplosiguientesonexclusivamenteilustrativos,no
resultadosempíricosquedebanreproducirse.
{
| "analysis_id": | "<UUID_ANALISIS>",          |             |                 |        |
| -------------- | --------------------------- | ----------- | --------------- | ------ |
| "user_id":     | "<UUID_USUARIO>",           |             |                 |        |
| "filename":    | "muestra.png",              |             |                 |        |
| "sha256":      | "<HASH_DEL_ARCHIVO>",       |             |                 |        |
| "technique":   | "lsb_statistical_analysis", |             |                 |        |
| "status":      | "sospechoso",               |             |                 |        |
| "indicators":  | {"anomaly_score":           | 0.82,       | "threshold":    | 0.75}, |
| "action":      | "cuarentena",               |             |                 |        |
| "limitations": | "Resultado                  | indicativo, | no concluyente" |        |
}
5.4 AnexoD.Escenariosmínimosdeprueba
LademostraciónfuncionaldeberáabarcarlosescenariosdelaTabla4.Elequipopodráampliarlacobertura
segúnsusriesgosytecnología,peronoreemplazarlaporcapturassinejecucióndemostrable.
| ID Escenario |     |     |     | Resultadomínimoesperado |
| ------------ | --- | --- | --- | ----------------------- |
T01 IniciarydetenerAUTHySTEGOporseparado. ProcesosyAPIsautónomos;integración
reproducible.
T02 Autenticarconcontraseñaválidaeinválida. JWTfirmadoorechazodeautenticación.
T03 ConsultarSTEGOsinJWT,conJWTmanipuladoo DenegaciónconHTTP401.
vencido.
T04 UsuarioconrolUSERintentaanalizarunaimagen. DenegaciónconHTTP403.
T05 Asignardosrolesaunusuarioyunrolados RelaciónN:Mpersistidaeíntegra.
usuarios.
DCCO|DesarrolloSoftwareSeguro Página6de8

ID Escenario Resultadomínimoesperado
T06 Repetirunaasignaciónusuario–rol. Nosegeneraunaasociaciónduplicada.
T07 RetirarunrolyreutilizarJWTtodavíavigente. Nuevaoperacióndenegadaporelpermiso
revocado.
T08 DejarAUTHtemporalmenteinaccesible. STEGOnoprocesasinautorizacióncomprobada.
T09 Analizarimagenoriginalyunamuestraconcarga Métricas,clasificaciónylimitaciones
LSB. documentadas.
T10 Subirarchivoinválido,corruptoodemasiado Rechazoseguro,sinprocesamientoindebido.
grande.
T11 Consultarunanálisisajenosinautorización. Accesodenegadosegúnlapolíticaderecursos.
T12 Revisarbitácorasdeaccesosyanálisis. TrazabilidadsinexponersecretosniJWTcompletos.
Cuadro4:Bateríamínimadepruebasdeautenticación,RBAC,integra-
ciónyesteganografía.
5.5 AnexoE.Matrizderiesgosdereferencia
ComopartedelprocesoShiftLeftSecurity,elequipodocumentarálosactivos,amenazasycontroles
previstosdesdeeldiseño.LaTabla5proporcionaunareferenciainicialquedeberáadaptarsealosriesgos
realmenteidentificadosyalaarquitecturaimplementada.
Activo Amenaza Controlesperado
Credencialese Suplantaciónydivulgación Hashseguro,validacionesylímitesdelogin.
identidades
AsignacionesN:M Elevacióndeprivilegios Integridadreferencial,autorizaciónvigentey
revocación.
JWTyclaves Falsificaciónofuga Firma,caducidad,verificacióndeclaimsy
secretoprotegido.
Comunicación Suplantacióndeservicio Identidaddeservicio,canalseguroy
AUTH–STEGO denegaciónpordefecto.
Archivose Cargamaliciosaoanálisisevasivo Validacióndearchivos,límitesy
imágenes procesamientoaislado.
Resultadosy Accesoindebido RBACporrecursoyauditoríasindatos
registros sensibles.
Cuadro5:Referenciasderiesgosycontrolesquedeberánjustificarseenelinformetécnico.
6. Bibliografía
[1] International Organization for Standardization (ISO) e International Electrotechnical Commis-
sion(IEC).(2022).ISO/IEC27001:2022.Informationsecurity,cybersecurityandprivacyprotection—
Information security management systems—Requirements. https://www.iso.org/standard/
27001
[2] InternationalOrganizationforStandardization(ISO)eInternationalElectrotechnicalCommission
(IEC).(2011).ISO/IEC27034-1:2011.Informationtechnology—Securitytechniques—Applicationsecurity—
Part1:Overviewandconcepts.https://www.iso.org/standard/44378.html
[3] OWASPFoundation.(2025).ApplicationSecurityVerificationStandard(ASVS),Version5.0.0.https:
//asvs.owasp.org/
[4] OWASP Foundation. (s. f.). File Upload Cheat Sheet. OWASP Cheat Sheet Series. https://
cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
DCCO|DesarrolloSoftwareSeguro Página7de8

[5] Jones,M.,Bradley,J.,ySakimura,N.(2015).JSONWebToken(JWT)(RFC7519).InternetEngineering
TaskForce.https://www.rfc-editor.org/rfc/rfc7519
[6] Jones,M.(2015).JSONWebKey(JWK)(RFC7517).InternetEngineeringTaskForce.https://www.
rfc-editor.org/rfc/rfc7517
[7] Sheffer,Y.,Hardt,D.,yJones,M.(2020).JSONWebTokenBestCurrentPractices(RFC8725).Internet
EngineeringTaskForce.https://www.rfc-editor.org/rfc/rfc8725
[8] Rose,S.,Borchert,O.,Mitchell,S.,yConnelly,S.(2020).ZeroTrustArchitecture(NISTSpecialPublica-
tion800-207).NationalInstituteofStandardsandTechnology.https://doi.org/10.6028/NIST.
SP.800-207
DCCO|DesarrolloSoftwareSeguro Página8de8