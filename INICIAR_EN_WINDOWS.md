# Ejecutar PYMES67 con IBM watsonx.ai

La aplicación sigue ejecutándose en tu computadora. Los tres planes se envían a IBM para
revisar su contenido; no se envía el nombre, el RFC ni el nombre del fundador en esa consulta.
Evita incluir datos personales en los planes.

## Configuración privada (una vez en cada computadora)

1. Instala Python 3 y abre PowerShell en la carpeta del proyecto.
2. Ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Si `.env` ya existe, no lo reemplaces: edítalo para completar las variables.
Reemplaza solamente `PEGA_AQUI_TU_CLAVE` por tu API key y guarda el archivo.
La región, el proyecto y el modelo del ejemplo corresponden a la configuración probada
en Prompt Lab para PYMES67. Si usas otra cuenta o proyecto, actualiza esos valores.
`.env` está excluido de Git. No guardes la clave en código, capturas ni GitHub.

## Iniciar

```powershell
.\.venv\Scripts\python.exe app.py
```

Abre http://127.0.0.1:5000 y mantén PowerShell abierto. Ctrl+C detiene el servidor.
Después de editar `.env`, detén y vuelve a iniciar el programa.
Es un servidor local de desarrollo; no se debe exponer directamente a internet.

## Qué evalúa

- Ventas: clientes, canales, acciones y metas, hasta 40 puntos.
- Finanzas: ingresos, costos, flujo y equilibrio, hasta 40 puntos.
- Mercado: segmento, demanda, competencia y diferenciación, hasta 20 puntos.
- Cada criterio de IA vale 0 a 5; el programa valida la estructura y los rangos y calcula la nota.
- Capital, giro, empleados y registro legal se usan como contexto para revisar coherencia, sin puntos propios. La nota total suma solo ventas (40), finanzas (40) y mercado (20).
- Las repeticiones evidentes reciben cero mediante validación local; si todos los planes son
  texto basura, no se consume una consulta de IBM.
- Para aprobar se requieren al menos 80/100 globales, al menos 80% en cada uno de los tres
  planes y ningún criterio de IA por debajo de 3/5. El capital no compensa un plan insuficiente.
- La revisión exige evidencia, cálculos, riesgos y coherencia entre los planes. Los supuestos
  sin sustento y las contradicciones reciben notas bajas, con explicación de qué falta.
- Los pasos 4 y 5, sus páginas y sus operaciones de servidor están bloqueados hasta aprobar.
  La aprobación corresponde a la empresa activa de la sesión, los datos actuales y la versión
  vigente de la rúbrica. Un resultado de una versión anterior requiere volver a evaluar.
- Si IBM falla o devuelve una respuesta inválida, no hay nueva nota: queda pendiente.
- Guardar nuevos parámetros invalida el resultado anterior.

La IA puede equivocarse y un buen puntaje no prueba que el negocio sea viable. Los datos siguen en memoria:
se pierden al reiniciar. Las consultas requieren internet y están sujetas a los límites de IBM.
La orientación de trámites tampoco verifica requisitos o precios actuales ante las autoridades.

## Guía de mejora por criterio

La evaluación incluye un desglose de los 12 criterios de contenido, con los mismos requisitos
que se envían a IBM: evidencia encontrada, motivo de la nota, brechas, 2 a 4 acciones concretas,
entregable esperado, comprobación y ejemplo orientativo. Los criterios débiles aparecen primero
y abiertos; puedes desplegar también las fortalezas. Los ejemplos no son evidencia ni deben
copiarse con cifras inventadas. La nueva evaluación revisará los cambios; la guía no garantiza aprobar.

Los textos sin contenido reciben una guía inicial basada en la rúbrica local, identificada como tal.
Las consultas ahora permiten respuestas más extensas; pueden tardar y consumir más tokens.
Una respuesta de IBM truncada o sin el desglose requerido no se acepta como evaluación completa.

Cada criterio ahora incluye estado del contenido y citas comprobadas contra los planes originales.
Se distingue contenido ausente, incompleto, contradictorio y completo sin autenticidad externa
verificada. Las referencias a información de otro plan cuentan: no hace falta duplicar un cálculo
o escenario en todos los campos. Se rechazan citas inexistentes, notas incompatibles con el estado
y explicaciones que repitan etiquetas de la plantilla. Esto no sustituye una auditoría humana.
La consulta de evaluación solicita a IBM una salida estructurada con un esquema JSON para
mantener consistentes los tipos de datos de los criterios, las citas y las acciones.
La variable WATSONX_EVALUATION_MODEL permite elegir el modelo de evaluación por separado del
modelo de trámites. La configuración de referencia usa mistralai/mistral-medium-2505 para
evaluación y conserva Granite para las otras consultas. Requiere acceso al modelo en tu región
y consume la cuota correspondiente a ese modelo; no se crean recursos de pago automáticamente.
Cada plan se analiza en una consulta separada, con los otros dos como contexto. Esto evita
mezclar criterios en una respuesta demasiado larga; puede aumentar el tiempo y el consumo de entrada.
Las citas se insertan desde fragmentos originales identificados por el programa: IBM selecciona
identificadores, sin reescribir el texto fuente. Esto evita citas inventadas o atribuidas al campo equivocado.
Las evaluaciones de versiones anteriores deben repetirse con esta rúbrica.

El archivo EJEMPLO_NORTE_CONTINUO.md contiene los campos de un caso simulado completo para
pruebas. Sus registros y proveedores son de demostración, no hechos reales. No hay aprobación garantizada.

## Comprobar sin consumir IBM

```powershell
.\.venv\Scripts\python.exe -m unittest test_integracion -v
```

Las pruebas simulan respuestas de IBM y comprueban puntajes, errores, validación y páginas.

## Paso 6: directorio de empresas

## Importar PDF y Word, y descargar resultados

En Parámetros puedes importar un PDF con texto o un Word .docx en cada apartado mediante
los tres importadores individuales. Si seleccionas un documento con los tres planes y sus
encabezados en líneas independientes, se extrae solo el apartado correspondiente al botón.
Se admite hasta 10 MB y 80 páginas por PDF. Los escaneos necesitan OCR previo y los archivos
.doc deben guardarse como .docx. Cada plan conserva el límite de 12000 caracteres. Revisa
el texto extraído y pulsa Guardar. La importación es local; IBM recibe el texto al evaluar.

Después de una evaluación completada, aprobada o no, aparece “Descargar evaluación completa
en PDF”. El informe incluye resultado, motivos de bloqueo, los 12 criterios, citas, acciones,
entregables, comprobaciones, ejemplos y un anexo con los textos evaluados. Descargarlo no
genera otra consulta de IBM. Requiere la misma sesión y que el resultado siga en memoria.

El expediente de prueba completo puede descargarse desde /ejemplo-prueba.pdf e importarse
en una sola operación. Incluye datos iniciales y los tres planes, con validación de demanda
complementaria realizada dentro del caso ficticio. No acredita hechos de una empresa real.

## Explorar el directorio

“⑥ Empresas” es de acceso libre, sin crear empresa ni aprobar. Solo editar la tarjeta requiere aprobación. El directorio muestra
las aprobaciones vigentes y 12 ejemplos ficticios identificados con calificaciones simuladas.
Incluye miniaturas locales por giro, empleados y solicitudes de financiamiento, inversión o personal.
Puedes buscar y filtrar por giro, oportunidad y origen. En “Editar la tarjeta y oportunidades”
puedes actualizar la descripción y lo que busca tu empresa. No se muestran RFC ni fundador.
Si cambias parámetros o dejas de aprobar, tu empresa deja de aparecer hasta volver a aprobar.
El directorio es de prueba, sin contactos ni operaciones financieras. Sus datos evaluados siguen
en memoria; al reiniciar se pierden. Los ejemplos permanecen porque forman parte del prototipo.

## Diagnóstico de conexión

- Configuración faltante: completa las cuatro variables en `.env`.
- 401: verifica o renueva la API key.
- 403: comprueba permisos y acceso al modelo.
- 400: revisa el modelo, proyecto y región según el código de Prompt Lab.
- 429: se alcanzó un límite de uso; revisa el plan y vuelve a intentar más tarde.

La clave fija de la versión anterior fue retirada del código. Si era tuya, revócala desde IBM:
eliminarla del archivo no la borra del historial de GitHub.


## Pantalla de bienvenida

La dirección / abre la bienvenida. Registrar empresa lleva al formulario original en /registrar-empresa; Explorar empresas abre /directorio-page sin registro. El logotipo permite volver a la bienvenida.
