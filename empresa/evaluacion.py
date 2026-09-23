"""
empresa/evaluacion.py
Motor de evaluación de viabilidad empresarial.

Califica la empresa en base a 7 parámetros con pesos configurables.
Cuando la empresa no aprueba, construye un prompt con los resultados
y lo envía a Bob para que genere feedback en lenguaje natural.

NOTA: Los pesos y la calificación mínima están marcados con TODO —
serán actualizados con los valores definitivos del documento de investigación
empresa_baja_california.docx en cuanto estén disponibles.
"""

import os
from datetime import datetime
from empresa import parametros as mod_parametros

# ── Configuración de la evaluación ──────────────────────────────────────────

# TODO: Ajustar pesos según empresa_baja_california.docx (deben sumar 100)
PESOS: dict[str, float] = {
    "capital_inicial":   20.0,
    "giro_sector":       10.0,
    "num_empleados":     10.0,
    "plan_ventas":       20.0,
    "plan_financiero":   20.0,
    "analisis_mercado":  15.0,
    "registro_legal":     5.0,
}

# TODO: Ajustar calificación mínima aprobatoria según empresa_baja_california.docx
CALIFICACION_MINIMA: float = 60.0

# Almacén de historial: { empresa_id: [lista de evaluaciones] }
_historial: dict[str, list] = {}


# ── Lógica de puntaje por parámetro ─────────────────────────────────────────

def calcular_puntaje_parametro(nombre_parametro: str, valor) -> float:
    """
    Calcula el puntaje obtenido para un parámetro individual.
    Retorna un valor entre 0.0 y el peso máximo del parámetro.

    Criterios por parámetro:
      - capital_inicial:  >= 50,000 MXN → 100%, >= 20,000 → 60%, < 20,000 → 20%
      - giro_sector:      sector con alta demanda en BC → 100%, media → 70%, baja → 40%
      - num_empleados:    >= 5 → 100%, >= 2 → 70%, 1 → 50%, 0 → 0%
      - plan_ventas:      >= 200 chars → 100%, >= 50 → 60%, < 50 → 20%
      - plan_financiero:  >= 200 chars → 100%, >= 50 → 60%, < 50 → 20%
      - analisis_mercado: >= 200 chars → 100%, >= 50 → 60%, < 50 → 20%
      - registro_legal:   True → 100%, False → 0%
    """
    peso = PESOS.get(nombre_parametro, 0.0)

    if nombre_parametro == "capital_inicial":
        if valor >= 50_000:
            factor = 1.0
        elif valor >= 20_000:
            factor = 0.6
        else:
            factor = 0.2

    elif nombre_parametro == "giro_sector":
        alta_demanda = {"tecnologia", "manufactura", "turismo", "agroindustria"}
        media_demanda = {"comercio", "construccion", "salud"}
        if valor in alta_demanda:
            factor = 1.0
        elif valor in media_demanda:
            factor = 0.7
        else:
            factor = 0.4

    elif nombre_parametro == "num_empleados":
        if valor >= 5:
            factor = 1.0
        elif valor >= 2:
            factor = 0.7
        elif valor == 1:
            factor = 0.5
        else:
            factor = 0.0

    elif nombre_parametro in ("plan_ventas", "plan_financiero", "analisis_mercado"):
        longitud = len(valor) if isinstance(valor, str) else 0
        if longitud >= 200:
            factor = 1.0
        elif longitud >= 50:
            factor = 0.6
        else:
            factor = 0.2

    elif nombre_parametro == "registro_legal":
        factor = 1.0 if valor else 0.0

    else:
        factor = 0.0

    return round(peso * factor, 2)


# ── Motor principal ──────────────────────────────────────────────────────────

def evaluar_empresa(empresa_id: str) -> dict:
    """
    Orquesta la evaluación completa de la empresa.

    Prerequisito: los 7 parámetros deben estar guardados.
    Retorna un dict con:
      - calificacion (float 0–100)
      - aprobado (bool)
      - detalle_puntajes (dict por parámetro)
      - feedback (str generado por Bob si no aprueba, vacío si aprueba)
      - fecha (str ISO)
    """
    if not mod_parametros.parametros_completos(empresa_id):
        return {"error": "Los 7 parámetros aún no han sido completados."}

    params = mod_parametros.obtener_parametros(empresa_id)

    detalle = {}
    calificacion_total = 0.0

    for nombre, peso in PESOS.items():
        valor = params.get(nombre)
        puntaje = calcular_puntaje_parametro(nombre, valor)
        detalle[nombre] = {
            "valor": valor,
            "puntaje_obtenido": puntaje,
            "puntaje_maximo": peso,
        }
        calificacion_total += puntaje

    calificacion_total = round(calificacion_total, 2)
    aprobado = calificacion_total >= CALIFICACION_MINIMA

    feedback = ""
    if not aprobado:
        feedback = generar_feedback(empresa_id, detalle, calificacion_total)

    resultado = {
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


def generar_feedback(empresa_id: str, detalle: dict, calificacion: float) -> str:
    """
    Construye un prompt con los resultados numéricos de la evaluación
    y lo envía a Bob para que genere recomendaciones en lenguaje natural.

    Si la API de Bob no está disponible, retorna un mensaje de texto plano
    con las áreas de oportunidad identificadas.
    """
    # Identificar parámetros que no alcanzaron el puntaje máximo
    areas_oportunidad = [
        f"- {nombre}: obtuvo {info['puntaje_obtenido']:.1f} de {info['puntaje_maximo']:.1f} puntos"
        for nombre, info in detalle.items()
        if info["puntaje_obtenido"] < info["puntaje_maximo"]
    ]

    prompt = (
        f"Eres un asesor de negocios experto en el contexto empresarial de Baja California, México.\n"
        f"Una empresa obtuvo una calificación de {calificacion:.1f}/100 en su evaluación de viabilidad, "
        f"cuando el mínimo aprobatorio es {CALIFICACION_MINIMA}.\n\n"
        f"Las áreas donde la empresa no alcanzó el puntaje máximo son:\n"
        + "\n".join(areas_oportunidad)
        + "\n\nPor favor proporciona recomendaciones específicas, prácticas y contextualizadas "
        f"a Baja California para que la empresa mejore cada una de estas áreas y pueda aprobar "
        f"la evaluación en su siguiente intento."
    )

    return _llamar_bob(prompt)


def _llamar_bob(prompt: str) -> str:
    """
    Envía el prompt a Bob y retorna la respuesta en texto.
    Usa la variable de entorno BOBSHELL_API_KEY para autenticación
    (la misma clave que usa Bob Shell — tipo Inference recomendado).
    Si la clave no está configurada, retorna el prompt como texto plano
    para que el equipo pueda verificar el contenido antes de integrar la API.
    """
    api_key = os.environ.get("BOBSHELL_API_KEY")

    if not api_key:
        # Modo sin API: retorna el prompt para revisión/desarrollo
        return (
            "[Bob no está configurado — establece BOBSHELL_API_KEY como variable de entorno]\n\n"
            + prompt
        )

    try:
        import urllib.request
        import json

        payload = json.dumps({"prompt": prompt}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.ibm.com/bob/v1/chat",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "Sin respuesta de Bob.")
    except Exception as exc:
        return f"[Error al contactar a Bob: {exc}]\n\n{prompt}"


# ── Historial ────────────────────────────────────────────────────────────────

def obtener_historial_evaluaciones(empresa_id: str) -> list:
    """
    Retorna la lista de todas las evaluaciones previas de la empresa.
    """
    return _historial.get(empresa_id, [])
