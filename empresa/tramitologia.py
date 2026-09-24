"""
empresa/tramitologia.py
Análisis de tramitología requerida según el giro del emprendimiento.

Usa el LLM en IBM watsonx para investigar los permisos, trámites y costos
específicos para Baja California según el sector del negocio.
"""

from empresa import parametros as mod_parametros
from empresa.evaluacion import _obtener_token_iam, _WATSONX_BASE_URL, _WATSONX_MODEL, _WATSONX_PROJECT_ID

# Almacén en memoria: { empresa_id: str (resultado) }
_cache_tramitologia: dict[str, str] = {}


# Contexto adicional por giro para enriquecer el prompt
_CONTEXTO_GIRO = {
    "comercio":      "tienda, local comercial, punto de venta al público",
    "manufactura":   "planta de producción, taller de manufactura, bodega industrial",
    "servicios":     "oficina de servicios, consultorio, despacho profesional",
    "tecnologia":    "oficina de tecnología, startup, empresa de software",
    "turismo":       "hotel, hostal, restaurante turístico, agencia de viajes",
    "agroindustria": "campo agrícola, empaque de productos, invernadero, rancho",
    "construccion":  "empresa constructora, contratista, obra civil",
    "salud":         "clínica, consultorio médico, laboratorio, farmacia",
    "educacion":     "escuela, centro de capacitación, academia, guardería",
    "otro":          "negocio en giro no clasificado",
}


def generar_tramitologia(empresa_id: str) -> dict:
    """
    Genera el análisis de tramitología para la empresa indicada.

    Retorna un dict con:
      - giro (str)
      - tramitologia (str — texto estructurado generado por el LLM)
      - error (str, solo si hubo un problema)
    """
    params = mod_parametros.obtener_parametros(empresa_id)
    if params is None:
        return {"error": "Los parámetros de la empresa no han sido registrados."}

    giro = params.get("giro_sector", "otro")
    contexto = _CONTEXTO_GIRO.get(giro, "negocio general")

    # Usar caché si ya fue generado para este empresa_id
    if empresa_id in _cache_tramitologia:
        return {"giro": giro, "tramitologia": _cache_tramitologia[empresa_id]}

    texto = _generar_con_llm(giro, contexto)
    _cache_tramitologia[empresa_id] = texto
    return {"giro": giro, "tramitologia": texto}


def _generar_con_llm(giro: str, contexto: str) -> str:
    """Llama al LLM y retorna el análisis de tramitología estructurado."""
    import urllib.request
    import json

    prompt = (
        f"Eres un experto en trámites empresariales de Baja California, México.\n"
        f"Un emprendedor quiere abrir un negocio de giro: {giro} ({contexto}).\n\n"
        f"Proporciona un análisis detallado de los trámites, permisos y costos necesarios "
        f"en Baja California para operar legalmente. Considera permisos municipales, "
        f"estatales y federales, incluyendo cuando aplique: licencia de funcionamiento, "
        f"uso de suelo, protección civil, COFEPRIS, IMSS, SAT, permisos de construcción, "
        f"verificación de suelo, certificaciones sanitarias y cualquier otro trámite relevante "
        f"para este giro específico.\n\n"
        "Responde EXACTAMENTE con el siguiente formato y nada más:\n\n"
        "RESUMEN\n"
        "<uno o dos párrafos de texto plano explicando el panorama general de trámites para este giro en BC>\n\n"
        "TRAMITES\n"
        "<nombre del trámite> | <institución responsable> | <costo aproximado en MXN o 'Sin costo'> | <tiempo estimado>\n"
        "<nombre del trámite> | <institución responsable> | <costo aproximado en MXN o 'Sin costo'> | <tiempo estimado>\n"
        "... (un trámite por línea, todos los que apliquen para este giro)\n\n"
        "No incluyas asteriscos, guiones, numeración, encabezados extra ni ningún otro formato. "
        "Solo texto plano en el resumen y el separador | en los trámites."
    )

    try:
        token = _obtener_token_iam()
        url = f"{_WATSONX_BASE_URL}/ml/v1/text/generation?version=2023-05-29"
        payload = json.dumps({
            "model_id": _WATSONX_MODEL,
            "project_id": _WATSONX_PROJECT_ID,
            "input": prompt,
            "parameters": {
                "max_new_tokens": 900,
                "temperature": 0.4,
            },
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["results"][0]["generated_text"].strip()
    except Exception as exc:
        return f"[Error al generar tramitología: {exc}]"
