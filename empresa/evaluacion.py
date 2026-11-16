"""Evaluación rigurosa del contenido de los tres planes con IBM."""

from empresa.revision_planes import revisar, CRITERIOS
from empresa.watsonx import ErrorWatsonx
from datetime import datetime
import hashlib
import json
from empresa import parametros as mod_parametros

# ── Configuración de la evaluación ──────────────────────────────────────────

# Solo se puntúa el contenido: los datos de la empresa son contexto, no puntos automáticos.
PESOS: dict[str, float] = {
    "plan_ventas": 40.0,
    "plan_financiero": 40.0,
    "analisis_mercado": 20.0,
}

CALIFICACION_MINIMA: float = 80.0
VERSION_EVALUACION = "contenido-v2"


def huella_parametros(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def comprobar_aprobacion(resultado):
    motivos = []
    if resultado.get("calificacion", 0) < CALIFICACION_MINIMA:
        motivos.append("Se requieren al menos 80/100 puntos globales.")
    for nombre in CRITERIOS:
        info = resultado.get("detalle_puntajes", {}).get(nombre, {})
        maximo = PESOS[nombre]
        if info.get("puntaje_obtenido", 0) < maximo * 0.8:
            motivos.append(f"{nombre.replace('_', ' ')}: se requiere al menos 80% en este plan.")
        criterios = info.get("criterios", {})
        if set(criterios) != CRITERIOS[nombre] or any(v < 3 for v in criterios.values()):
            motivos.append(f"{nombre.replace('_', ' ')}: ningún criterio puede quedar por debajo de 3/5.")
    return motivos


def acceso_aprobado(empresa_id):
    params = mod_parametros.obtener_parametros(empresa_id)
    historial = _historial.get(empresa_id, [])
    if not params or not historial:
        return False, "Primero completa y aprueba la evaluación rigurosa. Los pasos 4 y 5 están bloqueados."
    ultima = historial[-1]
    if (ultima.get("estado") != "completada" or ultima.get("version_evaluacion") != VERSION_EVALUACION
            or ultima.get("huella_parametros") != huella_parametros(params)):
        return False, "Debes volver a evaluar los datos actuales con los criterios rigurosos."
    motivos = comprobar_aprobacion(ultima)
    if not ultima.get("aprobado") or motivos:
        return False, "Evaluación no aprobada. " + " ".join(motivos)
    return True, "Evaluación rigurosa aprobada."

# Almacén de historial: { empresa_id: [lista de evaluaciones] }
_historial: dict[str, list] = {}


# ── Motor principal ──────────────────────────────────────────────────────────

def evaluar_empresa(empresa_id: str) -> dict:
    """
    Orquesta la evaluación completa de la empresa.

    Prerequisito: los 7 parámetros deben estar guardados.
    Retorna un dict con:
      - calificacion (float 0–100)
      - aprobado (bool)
      - detalle_puntajes (dict por parámetro)
      - feedback (str con recomendaciones de la revisión de contenido)
      - fecha (str ISO)
    """
    if not mod_parametros.parametros_completos(empresa_id):
        return {"error": "Los 7 parámetros aún no han sido completados."}

    params = mod_parametros.obtener_parametros(empresa_id)
    huella = huella_parametros(params)
    # Una nueva revisión deja sin efecto la aprobación previa mientras está en curso.
    _historial.setdefault(empresa_id, []).append({
        "aprobado": False, "estado": "pendiente", "fecha": datetime.utcnow().isoformat()
    })

    try:
        revision = revisar(params, PESOS)
    except ErrorWatsonx as exc:
        _historial.setdefault(empresa_id, []).append({
            "aprobado": False, "estado": "pendiente", "fecha": datetime.utcnow().isoformat()
        })
        return {"error": str(exc), "estado": "pendiente"}

    detalle = {}
    calificacion_total = 0.0

    for nombre, peso in PESOS.items():
        valor = params.get(nombre)
        puntaje = revision[nombre]["puntaje_obtenido"]
        detalle[nombre] = {
            "valor": valor,
            "puntaje_obtenido": puntaje,
            "puntaje_maximo": peso,
            **revision[nombre],
        }
        calificacion_total += puntaje

    calificacion_total = round(calificacion_total, 2)
    motivos = comprobar_aprobacion({"calificacion": calificacion_total, "detalle_puntajes": detalle})
    aprobado = not motivos
    if huella != huella_parametros(mod_parametros.obtener_parametros(empresa_id)):
        return {"error": "Los parámetros cambiaron durante la evaluación. Vuelve a evaluar.", "estado": "pendiente"}

    filas = [nombre.replace("_", " ") + " | " + info["mejora"].replace("|", "/").replace("\n", " ") for nombre, info in revision.items()]
    feedback = "RESUMEN\nEvaluación orientativa del contenido. No acredita la viabilidad ni verifica los datos declarados.\n\nTABLA\n" + "\n".join(filas)

    resultado = {
        "estado": "completada",
        "version_evaluacion": VERSION_EVALUACION,
        "huella_parametros": huella,
        "motivos_bloqueo": motivos,
        "guia_mejora": {nombre: {
            "puntaje": info["puntaje_obtenido"], "maximo": PESOS[nombre],
            "fuente": info["fuente"], "criterios": info["criterios"],
            "requisitos": info["requisitos"], "desglose": info["desglose"],
        } for nombre, info in revision.items()},
        "empresa_id": empresa_id,
        "calificacion": calificacion_total,
        "calificacion_minima": CALIFICACION_MINIMA,
        "aprobado": aprobado,
        "detalle_puntajes": detalle,
        "feedback": feedback,
        "fecha": datetime.utcnow().isoformat(),
    }

    # Guardar en historial
    if empresa_id not in _historial:
        _historial[empresa_id] = []
    _historial[empresa_id].append(resultado)

    return resultado



def obtener_historial_evaluaciones(empresa_id: str) -> list:
    """
    Retorna la lista de todas las evaluaciones previas de la empresa.
    """
    return _historial.get(empresa_id, [])
