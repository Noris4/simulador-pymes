# Simulador PyMES — Plan de Funciones (Backend Python)

## Visión General

El backend es una API REST en Python con **Flask** que sirve a una web app.
El flujo del usuario es lineal:

1. Crear un perfil de empresa
2. Recibir una guía paso a paso de requisitos legales y de negocio
3. Ingresar los parámetros evaluables
4. Ser evaluado por el motor de calificación (Bob)
5. Recibir feedback si reprueba, o avanzar al registro si aprueba

El backend se divide en **5 dominios funcionales**, cada uno implementado como un módulo Python independiente.

---

## Decisiones de Arquitectura Confirmadas

| Decisión | Elección |
|---|---|
| Framework web | **Flask** |
| Persistencia | **En memoria / archivos temporales** (base de datos se integrará en una fase futura) |
| Pesos de evaluación | Se definirán desde `empresa_baja_california.docx` (en elaboración) |
| Calificación mínima | Se definirá desde `empresa_baja_california.docx` (en elaboración) |
| Feedback de Bob | **Bob interpreta los resultados numéricos y genera respuestas en lenguaje natural** vía API |

---

## Sub-Tarea 1 — Perfil de Empresa

**Intent:** Crear, leer y actualizar el perfil básico de la empresa del usuario. Es el punto de entrada al sistema.

**Expected Outcomes:**
- El usuario puede crear un perfil con nombre, sector/giro y datos básicos del fundador.
- El perfil se puede recuperar y actualizar en cualquier momento.
- Cada perfil tiene un identificador único (`empresa_id`).

**Todo List:**
- [ ] Definir el modelo de datos `Empresa` (nombre, giro, fundador, fecha_creacion, estado)
- [ ] Implementar `crear_empresa(datos)` → crea y persiste un nuevo perfil
- [ ] Implementar `obtener_empresa(empresa_id)` → retorna el perfil completo
- [ ] Implementar `actualizar_empresa(empresa_id, datos)` → actualiza campos del perfil

**Relevant Context:**
- Módulo: `empresa/perfil.py`
- El `empresa_id` es usado por todos los demás módulos como referencia cruzada.

**Status:** `[ ] pending`

---

## Sub-Tarea 2 — Guía de Pasos

**Intent:** Proveer al usuario una guía estructurada, paso a paso, de lo que necesita hacer para crear una empresa en Baja California. Este módulo es informativo y pedagógico.

**Expected Outcomes:**
- El sistema puede devolver la lista ordenada de pasos del proceso de creación de empresa.
- Cada paso tiene un título, descripción, documentos requeridos y estado de completitud.
- El usuario puede marcar pasos como completados.

**Todo List:**
- [ ] Definir el modelo `Paso` (id, titulo, descripcion, documentos_requeridos, completado)
- [ ] Implementar `obtener_pasos()` → retorna la lista completa de pasos del proceso
- [ ] Implementar `obtener_paso(paso_id)` → retorna el detalle de un paso específico
- [ ] Implementar `marcar_paso_completado(empresa_id, paso_id)` → registra el avance del usuario
- [ ] Implementar `obtener_progreso(empresa_id)` → retorna cuántos pasos ha completado el usuario

**Relevant Context:**
- Módulo: `empresa/guia.py`
- Los pasos son fijos para Baja California (datos del `.docx` de investigación).
- El progreso es por `empresa_id`.

**Status:** `[ ] pending`

---

## Sub-Tarea 3 — Recolección de Parámetros

**Intent:** Capturar y validar los 7 parámetros evaluables que el usuario debe ingresar antes de la evaluación. Cada parámetro tiene formato y restricciones específicas.

**Expected Outcomes:**
- El usuario puede ingresar y actualizar cada parámetro de forma individual.
- El sistema valida que los datos sean del tipo y rango correcto antes de guardarlos.
- Se puede consultar el estado de completitud de los parámetros (cuáles faltan).

**Todo List:**
- [ ] Definir el modelo `Parametros` con los 7 campos:
  - `capital_inicial` (numérico, en MXN)
  - `giro_sector` (categoría de lista cerrada)
  - `num_empleados` (entero positivo)
  - `plan_ventas` (texto / puntuación)
  - `plan_financiero` (texto / puntuación)
  - `analisis_mercado` (texto / puntuación)
  - `registro_legal` (booleano / estado)
- [ ] Implementar `guardar_parametros(empresa_id, datos)` → persiste los parámetros
- [ ] Implementar `obtener_parametros(empresa_id)` → retorna los parámetros actuales
- [ ] Implementar `validar_parametros(datos)` → valida tipos, rangos y campos requeridos
- [ ] Implementar `parametros_completos(empresa_id)` → retorna True si los 7 parámetros están listos

**Relevant Context:**
- Módulo: `empresa/parametros.py`
- `parametros_completos()` es un prerequisito para iniciar la evaluación (Sub-Tarea 4).
- Los pesos de cada parámetro en la calificación se definen en la Sub-Tarea 4.

**Status:** `[ ] pending`

---

## Sub-Tarea 4 — Motor de Evaluación (Bob)

**Intent:** Calcular una calificación objetiva para la empresa con base en los 7 parámetros. Es el núcleo del sistema. Si la empresa no aprueba, Bob genera feedback específico y recomendaciones contextualizadas a Baja California.

**Expected Outcomes:**
- Dado un `empresa_id` con parámetros completos, el sistema produce una calificación numérica (0–100).
- Si la calificación es mayor o igual al mínimo aprobatorio, se habilita el registro legal.
- Si la calificación es menor, se genera una lista de observaciones por parámetro y recomendaciones de mejora.
- El historial de evaluaciones queda registrado.

**Todo List:**
- [ ] Definir los pesos de cada parámetro en la calificación (sumando 100%)
- [ ] Implementar `calcular_puntaje_parametro(nombre_parametro, valor)` → puntaje parcial por parámetro
- [ ] Implementar `evaluar_empresa(empresa_id)` → orquesta la evaluación completa y retorna calificación
- [ ] Implementar `generar_feedback(empresa_id, resultado_evaluacion)` → produce observaciones y recomendaciones por parámetro fallido
- [ ] Implementar `obtener_historial_evaluaciones(empresa_id)` → retorna evaluaciones previas
- [ ] Definir la constante `CALIFICACION_MINIMA` (valor a confirmar con el equipo)

**Relevant Context:**
- Módulo: `empresa/evaluacion.py`
- Los pesos exactos deben definirse a partir del `.docx` de investigación (`empresa_baja_california.docx`).
- **`generar_feedback()` construye un prompt estructurado con los puntajes por parámetro y lo envía a Bob; Bob interpreta los números y devuelve texto en lenguaje natural con observaciones y recomendaciones contextualizadas a Baja California.**
- `evaluar_empresa()` debe verificar `parametros_completos()` antes de proceder.

**Status:** `[ ] pending`

---

## Sub-Tarea 5 — Registro Legal

**Intent:** Una vez que la empresa aprueba la evaluación, guiar al usuario en el proceso formal de registro ante las autoridades de Baja California. Este módulo prepara y confirma el registro.

**Expected Outcomes:**
- Solo empresas con calificación aprobatoria pueden acceder al registro.
- El sistema puede generar un resumen/documento con los datos listos para el trámite oficial.
- El estado de la empresa se actualiza a "registrada" al completar el proceso.

**Todo List:**
- [ ] Implementar `verificar_elegibilidad_registro(empresa_id)` → confirma que la empresa aprobó la evaluación
- [ ] Implementar `preparar_documento_registro(empresa_id)` → compila todos los datos de la empresa en un resumen estructurado
- [ ] Implementar `confirmar_registro(empresa_id)` → marca la empresa como oficialmente registrada
- [ ] Implementar `obtener_estado_registro(empresa_id)` → retorna el estado actual del proceso de registro

**Relevant Context:**
- Módulo: `empresa/registro.py`
- `verificar_elegibilidad_registro()` debe consultar el resultado de `evaluar_empresa()` de la Sub-Tarea 4.
- El documento generado debe incluir: nombre, giro, CURP/RFC del fundador, capital, empleados y fecha.

**Status:** `[ ] pending`

---

## Resumen de Módulos y Funciones

| Módulo | Funciones |
|---|---|
| `empresa/perfil.py` | `crear_empresa`, `obtener_empresa`, `actualizar_empresa` |
| `empresa/guia.py` | `obtener_pasos`, `obtener_paso`, `marcar_paso_completado`, `obtener_progreso` |
| `empresa/parametros.py` | `guardar_parametros`, `obtener_parametros`, `validar_parametros`, `parametros_completos` |
| `empresa/evaluacion.py` | `calcular_puntaje_parametro`, `evaluar_empresa`, `generar_feedback`, `obtener_historial_evaluaciones` |
| `empresa/registro.py` | `verificar_elegibilidad_registro`, `preparar_documento_registro`, `confirmar_registro`, `obtener_estado_registro` |

---

## Decisiones Pendientes

- [ ] Pesos exactos de cada parámetro en la calificación (pendiente de `empresa_baja_california.docx`)
- [ ] Calificación mínima aprobatoria (pendiente de `empresa_baja_california.docx`)
- [ ] Esquema de base de datos para fase futura (SQLite o PostgreSQL)

---

## Notas de Implementación

- **Persistencia temporal**: Mientras no haya base de datos, los datos se mantienen en estructuras en memoria (diccionarios Python). Las funciones deben estar diseñadas de forma que el almacenamiento sea fácilmente intercambiable por una base de datos real en el futuro.
- **Integración de Bob en `generar_feedback()`**: La función construye un prompt estructurado con los resultados numéricos de cada parámetro (puntaje obtenido vs puntaje máximo, brecha, contexto de Baja California) y se lo envía a Bob. Bob devuelve texto en lenguaje natural con las observaciones y recomendaciones. La función retorna ese texto al frontend.
- **Separación de capas**: Cada módulo expone funciones Python puras. Las rutas HTTP de Flask se definen en un archivo `app.py` separado que únicamente llama a esas funciones — esto mantiene la lógica de negocio completamente independiente del framework web.
